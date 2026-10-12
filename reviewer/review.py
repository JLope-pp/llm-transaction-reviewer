import argparse
import json
import re
import statistics
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from data.load import load
from engine.keywords import label_all, normalize
from labels import ALL_GROUPS, CREDIT_ONLY, HIGH_RISK, is_credit, is_revenue, material_change
from reviewer.guardrails import plaid_contradiction, supports, supports_business
from reviewer.llm import LLM, CacheMiss, ProviderError, default_model, has_credentials, model_slug
from reviewer.prompt import PROMPT_VERSION, SYSTEM, TOOL, render_blind, render_second_look, render_user

DISTRESS = {"nsf", "overdraft"} | HIGH_RISK
AUTO_ADD_REVENUE = 0.85
AUTO_OTHER = 0.70
CHUNK = 30
SECOND_LOOK = True
BLIND_REVIEW = True
OUT_DIR = Path(__file__).parent.parent / "outputs"

INJECTION = re.compile(
    r"ignore (all |any )?(previous|prior|above)|instruction|system\s*:|system note|"
    r"(automated|ai) (reviewer|assistant)|note to (ai|reviewer)|label (this|it|as)|classify", re.I)


def _shape(desc: str) -> str:
    return " ".join([w for w in normalize(desc).split() if not re.search(r"\d", w)][:6])


def _counterparty(t: dict) -> str:
    pm = t["payment_meta"]
    who = pm.get("payer") if t["amount"] < 0 else pm.get("payee")
    who = who or t.get("merchant_name") or (t["counterparties"][0]["name"] if t["counterparties"] else "")
    return normalize(who or "")


def build_groups(business: dict, engine: dict) -> list[dict]:
    buckets = defaultdict(list)
    for t in business["transactions"]:
        e = engine[t["transaction_id"]]
        key = ("CREDIT" if t["amount"] < 0 else "DEBIT", _counterparty(t),
               _shape(t["original_description"]), e["group"], e["is_business"])
        buckets[key].append(t)
    holders = {a["account_id"]: a.get("holder_category") for a in business.get("accounts", [])}
    groups = []
    for i, (key, txns) in enumerate(sorted(buckets.items(), key=lambda kv: kv[1][-1]["date"])):
        amounts = [abs(t["amount"]) for t in txns]
        dates = sorted(date.fromisoformat(t["date"]) for t in txns)
        gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
        e = engine[txns[0]["transaction_id"]]
        cp = txns[0]["counterparties"][0] if txns[0]["counterparties"] else None
        pfc = txns[0]["personal_finance_category"]
        texts = [t["original_description"] for t in txns]
        bank_texts = [_without_memo(t) for t in txns]
        memos = [t["payment_meta"]["reason"] for t in txns if t["payment_meta"].get("reason")]
        groups.append({
            "ref": f"G{i + 1}",
            "direction": key[0],
            "transaction_ids": [t["transaction_id"] for t in txns],
            "stats": {
                "n": len(txns), "total": round(sum(amounts), 2), "min": min(amounts), "max": max(amounts),
                "distinct_amounts": len(set(amounts)), "first": dates[0].isoformat(),
                "last": dates[-1].isoformat(),
                "weekday_share": sum(d.weekday() < 5 for d in dates) / len(dates),
                "median_gap": f"{statistics.median(gaps):g}d" if gaps else "n/a",
            },
            "engine": {"group": e["group"], "is_business": e["is_business"], "matched": e["matched"]},
            "plaid": {
                "category": f"{pfc['detailed']} ({pfc['confidence_level']})" if pfc else "none",
                "counterparty": f"{cp['name']} ({cp['type']})" if cp else "none",
            },
            "descriptions": list(dict.fromkeys(texts))[:2],
            "memos": list(dict.fromkeys(memos))[:3],
            "suspicious_code": any(INJECTION.search(x) for x in texts + memos),
            "_counterparty": key[1],
            "_cp_type": cp["type"] if cp else None,
            "_pfc": pfc["detailed"] if pfc else None,
            "_pushed": key[0] == "DEBIT" and sum(
                (t["payment_meta"].get("payment_processor") or "").upper() in P2P_APPS
                for t in txns) * 2 >= len(txns),
            "_bank_texts": bank_texts,
            "_holder": holders.get(txns[0]["account_id"]),
        })
    returned = returned_debits(business)
    for g in groups:
        g["_returned"] = (g["direction"] == "CREDIT"
                          and sum(t in returned for t in g["transaction_ids"]) * 2 >= len(g["transaction_ids"]))
    add_facts(groups, business["meta"].get("owner_name"), business["meta"].get("name"))
    return groups


P2P_APPS = {"ZELLE", "VENMO", "CASH APP", "PAYPAL"}
PROCESSOR_TYPES = {"payment_terminal", "marketplace"}
TITLES = {"DR", "MR", "MRS", "MS"}


def _matches_owner(payer: str, owner: str | None) -> bool:
    if not owner or not payer:
        return False
    o = [w for w in normalize(owner).split() if w not in TITLES]
    p = payer.split()
    return len(o) >= 2 and len(p) >= 2 and p[-1] == o[-1] and (p[0] == o[0] or p[0] == o[0][0])


LEGAL_SUFFIXES = {"LLC", "INC", "CO", "PLLC", "CORP", "LTD"}


def _without_memo(t: dict) -> str:
    desc, memo = t["original_description"], t["payment_meta"].get("reason")
    if memo and memo in desc:
        desc = desc.replace(memo, " ")
    return desc.split(" MEMO:")[0].split(" OBI:")[0]


def _names_business(text: str, name: str | None) -> bool:
    words = [w for w in normalize(name or "").split() if w not in LEGAL_SUFFIXES]
    return len(words) >= 2 and f" {words[0]} {words[1]}" in f" {normalize(text)} "


RETURN_WINDOW_DAYS = 7


def end_of_day_balances(business: dict) -> dict[str, float] | None:
    hb = business.get("historical_balances")
    if not hb:
        return None
    return {h["date"]: h["current"] for h in next(iter(hb.values()))}


def returned_debits(business: dict) -> dict[str, str]:
    balances = end_of_day_balances(business)
    txns = business["transactions"]
    debits = [t for t in txns if t["amount"] > 0 and t["payment_channel"] == "other"]
    out = {}
    for c in (t for t in txns if t["amount"] < 0):
        cd, text = date.fromisoformat(c["date"]), normalize(c["original_description"])
        for d in debits:
            dd = date.fromisoformat(d["date"])
            if d["transaction_id"] in out.values() or abs(d["amount"] + c["amount"]) > 0.005:
                continue
            if not 0 <= (cd - dd).days <= RETURN_WINDOW_DAYS:
                continue
            first = _counterparty(d).split()[:1]
            if not first or len(first[0]) < 3 or f" {first[0]} " not in f" {_counterparty(c)} {text} ":
                continue
            if balances is not None and not any(
                    balances.get((dd + timedelta(k)).isoformat(), 0) - (-c["amount"] if dd + timedelta(k) >= cd else 0) < 0
                    for k in range((cd - dd).days + 1)):
                continue
            out[c["transaction_id"]] = d["transaction_id"]
            break
    return out


def add_facts(groups: list[dict], owner: str | None, business_name: str | None = None) -> None:
    by_cp = defaultdict(list)
    for g in groups:
        if g["_counterparty"]:
            by_cp[g["_counterparty"]].append(g)
    for g in groups:
        facts = []
        if g.get("_returned"):
            facts.append("these credits give back earlier debits of the same amount to the same counterparty, "
                         "while the balance was negative: returned (bounced) payments")
        for o in by_cp.get(g["_counterparty"], []) if not g.get("_returned") else []:
            lump, fixed = (g, o) if g["direction"] == "CREDIT" else (o, g)
            if (o["direction"] != g["direction"] and lump["stats"]["n"] <= 3 and not fixed["_pushed"]
                    and fixed["stats"]["n"] >= 5 and fixed["stats"]["distinct_amounts"] <= 2):
                s = o["stats"]
                facts.append(f"same counterparty also has {s['n']} {o['direction']} txns, "
                             f"${s['min']:,.2f}-${s['max']:,.2f} ({s['distinct_amounts']} distinct), "
                             f"weekdays {s['weekday_share']:.0%}, median gap {s['median_gap']}, "
                             f"{s['first']}..{s['last']}")
        if g["direction"] == "CREDIT" and _matches_owner(g["_counterparty"], owner):
            facts.append(f"payer matches the owner on the application ({owner})")
        g["_names_business"] = g["direction"] == "CREDIT" and any(
            _names_business(x, business_name) for x in g["_bank_texts"])
        if g["direction"] == "CREDIT" and g["_cp_type"] in PROCESSOR_TYPES:
            facts.append(f"counterparty is a payment processor/marketplace (Plaid type {g['_cp_type']})")
        g["facts"] = facts


def validate(tool_input, refs: set[str]) -> tuple[dict, list[str]]:
    errors, good = [], {}
    items = tool_input.get("reviews") if isinstance(tool_input, dict) else None
    if not isinstance(items, list):
        return {}, ["no 'reviews' array"]
    for r in items:
        if not isinstance(r, dict) or r.get("ref") not in refs:
            errors.append(f"unknown or missing ref: {r.get('ref') if isinstance(r, dict) else r}")
            continue
        problems = []
        if "verdict" in TOOL["inputSchema"]["json"]["properties"]["reviews"]["items"]["properties"] \
                and r.get("verdict") not in ("agree", "flag"):
            problems.append("verdict")
        if r.get("group") not in ALL_GROUPS:
            problems.append(f"group {r.get('group')!r} not in enum")
        if not isinstance(r.get("is_business"), bool):
            problems.append("is_business")
        c = r.get("confidence")
        if not isinstance(c, (int, float)) or not 0 <= c <= 1:
            problems.append("confidence not in [0,1]")
        if not isinstance(r.get("reason"), str) or not r["reason"].strip():
            problems.append("reason")
        if problems:
            errors.append(f"{r['ref']}: {', '.join(problems)}")
        else:
            good[r["ref"]] = {**r, "reason": r["reason"].strip()[:200],
                              "suspicious_text": bool(r.get("suspicious_text", False))}
    missing = refs - set(good)
    if missing:
        errors.append(f"missing reviews for {', '.join(sorted(missing, key=lambda x: int(x[1:])))}")
    return good, errors


def review_chunk(llm: LLM, meta: dict, chunk: list[dict], log: list) -> dict:
    refs = {g["ref"] for g in chunk}
    good, note = {}, ""
    for attempt in range(2):
        user = render_user(meta, chunk, note)
        try:
            rec = llm.call(SYSTEM, user, TOOL)
        except ProviderError as e:
            if len(chunk) > 1:
                log.append({"refs": sorted(refs), "split_after": f"{type(e).__name__}: {e}"[:200]})
                half = len(chunk) // 2
                for part in (chunk[:half], chunk[half:]):
                    good.update(review_chunk(llm, meta, part, log))
                return good
            log.append({"refs": sorted(refs), "error": f"{type(e).__name__}: {e}"})
            return good
        except CacheMiss as e:
            log.append({"refs": sorted(refs), "error": f"{type(e).__name__}: {e}"})
            return good
        got, errors = validate(rec["tool_input"], refs)
        good.update({k: v for k, v in got.items() if k not in good})
        log.append({"refs": sorted(refs), "attempt": attempt, "errors": errors,
                    "usage": rec["usage"], "cost_usd": rec.get("cost_usd", 0)})
        if not (refs - set(good)) and not errors:
            break
        note = "; ".join(errors)[:800]
    return good


def _suspicious(g: dict, r: dict | None) -> bool:
    return g["suspicious_code"] or bool(r and r.get("suspicious_text"))


def second_look(llm: LLM, meta: dict, groups: list[dict], reviews: dict, log: list) -> None:
    for g in groups:
        r = reviews.get(g["ref"])
        if not r or _suspicious(g, r):
            continue
        e = g["engine"]
        same_label = (r["group"], r["is_business"]) == (e["group"], e["is_business"])
        alts = plaid_contradiction(g)
        if alts and _effective(r, e)["group"] not in alts:
            g["plaid_contradiction"] = alts
            user = render_second_look(meta, g, r, alts)
        elif r.get("verdict") == "flag" and same_label:
            user = render_second_look(meta, g, r)
        else:
            continue
        try:
            rec = llm.call(SYSTEM, user, TOOL)
        except (CacheMiss, ProviderError) as ex:
            log.append({"refs": [g["ref"]], "second_look": True, "error": f"{type(ex).__name__}: {ex}"})
            continue
        got, errors = validate(rec["tool_input"], {g["ref"]})
        log.append({"refs": [g["ref"]], "second_look": True, "errors": errors,
                    "usage": rec["usage"], "cost_usd": rec.get("cost_usd", 0)})
        if g["ref"] in got:
            reviews[g["ref"]] = {**got[g["ref"]], "second_look": True}


def _effective(review: dict, engine: dict) -> dict:
    if review.get("verdict") == "agree":
        return engine
    return {"group": review["group"], "is_business": review["is_business"]}


def blind_review(llm: LLM, meta: dict, groups: list[dict], reviews: dict, log: list) -> None:
    for g in groups:
        r = reviews.get(g["ref"])
        suspicious = _suspicious(g, r)
        if not suspicious and not (g["memos"] and r):
            continue
        try:
            rec = llm.call(SYSTEM, render_blind(meta, g), TOOL)
        except (CacheMiss, ProviderError) as ex:
            log.append({"refs": [g["ref"]], "blind": True, "error": f"{type(ex).__name__}: {ex}"})
            continue
        got, errors = validate(rec["tool_input"], {g["ref"]})
        log.append({"refs": [g["ref"]], "blind": True, "errors": errors,
                    "usage": rec["usage"], "cost_usd": rec.get("cost_usd", 0)})
        if g["ref"] not in got:
            continue
        blind, first = got[g["ref"]], r or {}
        if not suspicious:
            sign = -1 if g["direction"] == "CREDIT" else 1
            blind_label = {"group": blind["group"], "is_business": blind["is_business"]}
            if not material_change(sign, _effective(r, g["engine"]), blind_label):
                continue
        reviews[g["ref"]] = {**blind, "blind": True, "suspicious_text": True,
                             "text_dependent": not suspicious, "first_reason": first.get("reason")}


def decide(group: dict, review: dict | None, txn: dict, engine_label: dict) -> dict:
    eng = {"group": engine_label["group"], "is_business": engine_label["is_business"]}
    out = {"engine": {**eng, "revenue": engine_label["revenue"]}, "proposed": None, "final": dict(eng), "status": "unreviewed",
           "confidence": None, "reason": None, "group_ref": group["ref"],
           "suspicious_text": group["suspicious_code"]}
    if review is None:
        return out
    prop = {"group": review["group"], "is_business": review["is_business"]}
    for k in ("second_look", "blind", "text_dependent", "first_reason"):
        if review.get(k):
            out[k] = review[k]
    if group.get("plaid_contradiction"):
        out["plaid_contradiction"] = group["plaid_contradiction"]
    if review.get("text_dependent"):
        review = {**review, "reason": f"Payer text changes the credit outcome. With the text: "
                                      f"{review.get('first_reason')} | Without it: {review['reason']}"}
    out.update(confidence=review["confidence"], reason=review["reason"],
               suspicious_text=group["suspicious_code"] or review["suspicious_text"])
    discard = None
    if prop == eng or review.get("verdict") == "agree":
        discard = "agree"
    elif prop["group"] in CREDIT_ONLY and not is_credit(txn["amount"]):
        discard = f"direction: {prop['group']} on a debit"
    elif not material_change(txn["amount"], eng, prop):
        discard = f"immaterial: {prop['group']}/{prop['is_business']}"
    if discard:
        out["status"] = "needs_review" if out["suspicious_text"] else "agree"
        if discard != "agree":
            out["discarded"] = discard
        return out
    out["proposed"] = {**prop, "revenue": is_revenue(txn["amount"], prop["group"], prop["is_business"])}
    applied, missing = dict(eng), []
    if prop["group"] != eng["group"]:
        out["evidence_group"] = supports(group, prop["group"])
        if out["evidence_group"]:
            applied["group"] = prop["group"]
        else:
            missing.append(f"group {prop['group']}")
    if prop["is_business"] != eng["is_business"]:
        out["evidence_business"] = supports_business(group, prop["is_business"])
        if out["evidence_business"]:
            applied["is_business"] = prop["is_business"]
        else:
            missing.append("business" if prop["is_business"] else "personal")
    adds_revenue = (is_revenue(txn["amount"], applied["group"], applied["is_business"])
                    and not is_revenue(txn["amount"], eng["group"], eng["is_business"]))
    bar = AUTO_ADD_REVENUE if adds_revenue else AUTO_OTHER
    if eng["group"] in DISTRESS and applied["group"] not in DISTRESS:
        missing.append(f"removing {eng['group']}")
        applied["group"] = eng["group"]
    if review.get("blind") and missing:
        out["proposed"] = None
        out["status"], out["held"] = "needs_review", f"suspicious text; blind proposal not backed ({', '.join(missing)})"
    elif out["suspicious_text"]:
        out["status"], out["held"] = "needs_review", "suspicious text"
    elif review["confidence"] < bar:
        out["status"], out["held"] = "needs_review", f"confidence {review['confidence']} < {bar}"
    elif applied == eng or not material_change(txn["amount"], eng, applied):
        out["status"], out["held"] = "needs_review", f"no structured evidence for {', '.join(missing)}"
    else:
        out["status"], out["final"] = "corrected", applied
        if missing:
            out["held"] = f"not applied, no structured evidence for {', '.join(missing)}"
    return out


def review_business(llm: LLM, business: dict, log: list) -> tuple[dict, list[dict]]:
    engine = label_all(business["transactions"])
    groups = build_groups(business, engine)
    reviews = {}
    for i in range(0, len(groups), CHUNK):
        reviews.update(review_chunk(llm, business["meta"], groups[i:i + CHUNK], log))
    if SECOND_LOOK:
        second_look(llm, business["meta"], groups, reviews, log)
    if BLIND_REVIEW:
        blind_review(llm, business["meta"], groups, reviews, log)
    by_id = {t["transaction_id"]: t for t in business["transactions"]}
    results = {}
    for g in groups:
        for tid in g["transaction_ids"]:
            d = decide(g, reviews.get(g["ref"]), by_id[tid], engine[tid])
            final = d["final"]
            d["final"]["revenue"] = is_revenue(by_id[tid]["amount"], final["group"], final["is_business"])
            results[tid] = d
    return results, groups


def run(model_id: str, offline: bool, input_path=None, out_dir=None, businesses=None) -> dict:
    if not offline and not has_credentials(model_id):
        print(f"No credentials for {model_id}: replaying from cache only. Groups not in the cache "
              f"keep the engine label (status unreviewed). Set AWS_BEARER_TOKEN_BEDROCK + AWS_REGION "
              f"or ANTHROPIC_API_KEY to review new transactions.", file=sys.stderr)
        offline = True
    llm = LLM(model_id, offline=offline)
    businesses = businesses or (load(input_path) if input_path else load())
    log, results, group_dump = [], {}, {}
    for b in businesses:
        r, groups = review_business(llm, b, log)
        results.update(r)
        group_dump[b["business_id"]] = [{k: g[k] for k in ("ref", "direction", "stats", "engine", "facts",
                                                           "descriptions", "suspicious_code")} for g in groups]
    spend = sum(x.get("cost_usd", 0) for x in log)
    summary = {
        "model": model_id, "prompt_version": PROMPT_VERSION, "second_look": SECOND_LOOK, "offline": offline,
        "second_look_calls": sum(bool(x.get("second_look")) for x in log),
        "blind_calls": sum(bool(x.get("blind")) for x in log),
        "transactions": len(results),
        "excluded_pending": {b["business_id"]: b["excluded_pending"] for b in businesses if b["excluded_pending"]},
        "status_counts": {s: sum(r["status"] == s for r in results.values())
                          for s in ("agree", "corrected", "needs_review", "unreviewed")},
        "llm_calls": llm.calls, "invalid_attempts": sum(bool(x.get("errors")) for x in log),
        "errors": [x for x in log if x.get("error")],
        "chunk_splits": [x for x in log if x.get("split_after")],
        "spend_usd_this_run_incl_cache": round(spend, 4),
        "tokens": {k: sum(x.get("usage", {}).get(k, 0) for x in log) for k in ("inputTokens", "outputTokens")},
    }
    out = Path(out_dir) if out_dir else OUT_DIR / model_slug(model_id)
    out.mkdir(parents=True, exist_ok=True)
    (out / "reviews.json").write_text(json.dumps(results, indent=1))
    (out / "groups.json").write_text(json.dumps(group_dump, indent=1))
    (out / "run_summary.json").write_text(json.dumps(summary, indent=1))
    return summary


def main():
    ap = argparse.ArgumentParser(description='LLM reviewer: flags keyword-engine labels it doubts.')
    ap.add_argument("--model", default=default_model())
    ap.add_argument("--offline", action="store_true", help="cache only; never call the provider")
    ap.add_argument("--input", help="a /transactions/get JSON file or a generated folder")
    a = ap.parse_args()
    print(json.dumps(run(a.model, a.offline, a.input), indent=1))


if __name__ == "__main__":
    main()
