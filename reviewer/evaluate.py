import argparse
import json
from pathlib import Path
from collections import Counter, defaultdict

import re

from data.load import load, load_truth
from engine.keywords import label_all
from credit.features import coverage_days
from labels import ALL_GROUPS, is_revenue, material_change
from reviewer.llm import default_model, model_slug
from reviewer.review import OUT_DIR

ALIASES = {
    "notaveragemonthlyrevenue": "not_revenue", "notrevenue": "not_revenue", "nonrevenue": "not_revenue",
    "revenueverification": "revenue_verification", "revenue": "revenue_verification",
    "nsf": "nsf", "nsfs": "nsf", "overdraft": "overdraft", "overdrafts": "overdraft",
    "internaltransfer": "internal_transfer", "transfer": "internal_transfer", "ucc": "ucc",
    "activeadvance": "active_advance", "advance": "active_advance", "mca": "active_advance",
    "autodeposit": "auto_deposit",
    "highriskgambling": "hr_gambling", "gambling": "hr_gambling",
    "highriskbankruptcy": "hr_bankruptcy", "bankruptcy": "hr_bankruptcy",
    "highriskdebtsettlementpayments": "hr_debt_settlement", "highriskdebtsettlement": "hr_debt_settlement",
    "debtsettlement": "hr_debt_settlement",
    "highriskgarnishment": "hr_garnishment", "garnishment": "hr_garnishment",
    "highriskother": "hr_other",
    "none": "none", "": "none", "ordinary": "none", "other": "none", "nogroup": "none",
}
ALIASES.update({re.sub(r"[^a-z0-9]", "", g): g for g in ALL_GROUPS})


def _pick(d: dict, *names):
    return next((d[n] for n in names if n in d), None)


def read_truth(path) -> tuple[dict, list[str]]:
    obj = json.loads(Path(path).read_text())
    if isinstance(obj, dict):
        obj = _pick(obj, "labels", "truth", "transactions") or obj
    items = (list(obj.items()) if isinstance(obj, dict)
             else [(_pick(x, "transaction_id", "id", "txn_id"), x) for x in obj])
    truth, unknown, revenue_only, notes = {}, set(), 0, []
    for tid, lab in items:
        lab = lab if isinstance(lab, dict) else {"group": lab}
        raw = _pick(lab, "group", "label", "category", "group_name")
        rev = _pick(lab, "revenue", "is_revenue")
        biz = _pick(lab, "is_business", "business")
        if biz is None and "personal" in lab:
            biz = not lab["personal"]
        if isinstance(biz, str):
            biz = biz.strip().lower() != "personal"
        if raw is None and rev is not None:
            group, revenue_only = ("none" if rev else "not_revenue"), revenue_only + 1
        else:
            group = ALIASES.get(re.sub(r"[^a-z0-9]", "", str(raw or "").lower()))
            if group is None:
                unknown.add(str(raw))
                continue
        truth[tid] = {"group": group, "is_business": True if biz is None else bool(biz),
                      "revenue": rev, "case": str(_pick(lab, "case", "note") or "")}
    if unknown:
        notes.append(f"unknown group names skipped: {sorted(unknown)}")
    if revenue_only:
        notes.append(f"{revenue_only} labels give revenue only: group metrics are approximate")
    return truth, notes


def complete_truth(businesses, truth) -> tuple[dict, list[str]]:
    full, missing = dict(truth), 0
    for b in businesses:
        engine = label_all(b["transactions"])
        for t in b["transactions"]:
            if t["transaction_id"] not in full:
                full[t["transaction_id"]] = {**engine[t["transaction_id"]], "case": "not_in_truth"}
                missing += 1
    return full, [f"{missing} transactions not in the truth file: scored as the engine labeled them"] if missing else []


def top_errors(businesses, truth, reviews, n=10) -> list[dict]:
    agg = {}
    for b in businesses:
        for t in b["transactions"]:
            tid = t["transaction_id"]
            tr, r = truth.get(tid), reviews.get(tid)
            if not tr or not r or not material_change(t["amount"], r["final"], tr):
                continue
            outcome = ("missed" if r["status"] in ("agree", "unreviewed")
                       else "held for underwriter" if r["status"] == "needs_review" else "wrong correction")
            rev_f = is_revenue(t["amount"], r["final"]["group"], r["final"]["is_business"])
            rev_t = is_revenue(t["amount"], tr["group"], tr["is_business"])
            effect = "false revenue" if rev_f and not rev_t else "missed revenue" if rev_t and not rev_f else "risk signal"
            key = (b["business_id"], r["group_ref"], r["final"]["group"], tr["group"])
            row = agg.setdefault(key, {"business": b["business_id"], "description": t["original_description"],
                                       "engine": r["engine"]["group"],
                                       "proposed": (r["proposed"] or {}).get("group"),
                                       "final": r["final"]["group"], "truth": tr["group"], "outcome": outcome,
                                       "effect": effect, "reason": r["reason"], "held": r.get("held"),
                                       "n": 0, "usd": 0.0})
            row["n"] += 1
            row["usd"] = round(row["usd"] + abs(t["amount"]), 2)
    return sorted(agg.values(), key=lambda x: -x["usd"])[:n]


def _label_wrong(label, truth, amount):
    return (label["group"] != truth["group"] or label["is_business"] != truth["is_business"])


def _material(label, truth, amount):
    return material_change(amount, label, truth)


def evaluate(model_id: str, data=None, out_dir=None, truth=None, businesses=None) -> dict:
    out = Path(out_dir) if out_dir else OUT_DIR / model_slug(model_id)
    reviews = json.loads((out / "reviews.json").read_text())
    if truth is None:
        truth = load_truth(data) if data else load_truth()
    rows, per_biz = [], {}
    for b in businesses or (load(data) if data else load()):
        days = coverage_days(b)
        engine = label_all(b["transactions"])
        rev, gross = defaultdict(float), defaultdict(float)
        for t in b["transactions"]:
            tid, amt = t["transaction_id"], t["amount"]
            tr, r = truth[tid], reviews[tid]
            accepted = r["proposed"] or r["engine"]
            for name, lab in (("truth", tr), ("engine", engine[tid]), ("auto", r["final"]), ("accept_all", accepted)):
                if is_revenue(amt, lab["group"], lab["is_business"]):
                    rev[name] += -amt
                if is_revenue(amt, lab["group"], lab["is_business"]) != is_revenue(amt, tr["group"], tr["is_business"]):
                    gross[name] += abs(amt)
            rows.append({"biz": b["business_id"], "tid": tid, "amount": amt, "case": tr.get("case", ""),
                         "truth": tr, "engine": engine[tid], "review": r})
        m = 30.4 / days
        per_biz[b["business_id"]] = ({k: round(v * m) for k, v in rev.items()} | {"days": days}
                                     | {f"gross_error_{k}": round(v * m) for k, v in gross.items()})

    def err(name):
        return {k: v[name] - v["truth"] for k, v in per_biz.items()}

    flagged = [x for x in rows if x["review"]["status"] in ("corrected", "needs_review")]
    eng_wrong = [x for x in rows if _label_wrong(x["engine"], x["truth"], x["amount"])]
    eng_material = [x for x in rows if _material(x["engine"], x["truth"], x["amount"])]
    tp = [x for x in flagged if _label_wrong(x["engine"], x["truth"], x["amount"])]
    fixed = [x for x in flagged if x["review"]["proposed"]
             and not _label_wrong(x["review"]["proposed"], x["truth"], x["amount"])]
    material_caught = [x for x in eng_material if x["review"]["status"] in ("corrected", "needs_review")]
    hard_neg = [x for x in rows if "hard_negative" in x["case"]
                or ("injection" in x["case"] and not _label_wrong(x["engine"], x["truth"], x["amount"]))]
    broke = [x for x in rows if x["review"]["status"] == "corrected"
             and not _label_wrong(x["engine"], x["truth"], x["amount"])]
    corrected = [x for x in rows if x["review"]["status"] == "corrected"]
    harmful = [x for x in corrected if _material(x["review"]["final"], x["truth"], x["amount"])
               and not _material(x["engine"], x["truth"], x["amount"])]
    still_wrong = [x for x in corrected if _material(x["review"]["final"], x["truth"], x["amount"])]

    summary = {
        "model": model_id,
        "monthly_revenue_by_business": per_biz,
        "gross_dollar_error_per_month": {
            name: sum(v.get(f"gross_error_{name}", 0) for v in per_biz.values())
            for name in ("engine", "auto", "accept_all")},
        "abs_dollar_error_per_month": {
            name: {"total": sum(abs(v) for v in err(name).values()),
                   "by_business": err(name)} for name in ("engine", "auto", "accept_all")},
        "transactions": len(rows),
        "engine_wrong": len(eng_wrong), "engine_material_wrong": len(eng_material),
        "flags": len(flagged), "flag_precision": round(len(tp) / max(len(flagged), 1), 3),
        "recall_any_error": round(len(tp) / max(len(eng_wrong), 1), 3),
        "recall_material": round(len(material_caught) / max(len(eng_material), 1), 3),
        "proposals_exactly_right": len(fixed),
        "auto_corrections_that_broke_a_correct_label": len(broke),
        "auto_corrections_made_materially_wrong": len(harmful),
        "auto_corrections_still_materially_wrong": len(still_wrong),
        "harmful_by_case": Counter(f"{x['case']}: engine {x['engine']['group']} -> {x['review']['final']['group']}"
                                   f" (truth {x['truth']['group']})" for x in harmful + still_wrong).most_common(10),
        "status_counts": Counter(x["review"]["status"] for x in rows),
        "hard_negatives": {"n": len(hard_neg),
                           "flagged": sum(x["review"]["status"] in ("corrected", "needs_review") for x in hard_neg),
                           "cases": Counter(x["case"] for x in hard_neg
                                            if x["review"]["status"] in ("corrected", "needs_review"))},
        "injection_cases": [{
            "case": x["case"], "truth": x["truth"]["group"], "engine": x["engine"]["group"],
            "status": x["review"]["status"], "proposed": x["review"]["proposed"],
            "final": x["review"]["final"]["group"], "suspicious": x["review"]["suspicious_text"],
            "reason": x["review"]["reason"]} for x in rows if "injection" in x["case"]],
        "misses_by_case": Counter(f"{x['case']}: {x['truth']['group']} (engine {x['engine']['group']})"
                                  for x in eng_material if x not in material_caught).most_common(15),
        "false_flags_by_case": Counter(f"{x['case']}: engine {x['engine']['group']} -> "
                                       f"{(x['review']['proposed'] or {}).get('group')}"
                                       for x in flagged if x not in tp).most_common(15),
        "wrong_proposals_by_case": Counter(
            f"{x['case']}: truth {x['truth']['group']}/{x['truth']['is_business']} proposed "
            f"{x['review']['proposed']['group']}/{x['review']['proposed']['is_business']}"
            for x in tp if x not in fixed and x["review"]["proposed"]).most_common(15),
    }
    (out / "metrics.json").write_text(json.dumps(summary, indent=1, default=dict))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=default_model())
    print(json.dumps(evaluate(ap.parse_args().model), indent=1, default=dict))


if __name__ == "__main__":
    main()
