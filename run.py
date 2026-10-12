import argparse
import json
import sys
from pathlib import Path

from credit import simulate
from credit.decision import decide
from credit.features import features
from data.load import load
from engine.keywords import label_all
from reviewer import evaluate, review
from reviewer.llm import CACHE_DIR, CACHED_MODEL, default_model, model_slug
OUT = Path(__file__).parent / "outputs"


def spend() -> dict:
    return {f.stem: round(sum(json.loads(l).get("cost_usd", 0) for l in f.open()), 4)
            for f in sorted(CACHE_DIR.glob("*.jsonl"))}


def summary(model_id: str, m: dict, ba: dict) -> str:
    rows = ["", f"Reviewer: {model_id}", "",
            f"{'Biz':4} {'Monthly revenue':>34}   {'Offer':>34}",
            f"{'':4} {'truth':>10} {'engine':>11} {'reviewer':>11}   {'truth':>10} {'engine':>11} {'reviewer':>11}"]
    for biz, v in ba["by_business"].items():
        t, e, a = v["truth"], v["engine"], v["auto"]
        rows.append(f"{biz:4} {t['monthly_revenue']:>10,} {e['monthly_revenue']:>11,} {a['monthly_revenue']:>11,}   "
                    f"{t['offer']:>10,} {e['offer']:>11,} {a['offer']:>11,}")
    err = m["abs_dollar_error_per_month"]
    s = ba["summary"]
    hn = m["hard_negatives"]
    rows += ["",
             f"Monthly revenue error, sum of |error| per business: engine ${err['engine']['total']:,}"
             f" -> reviewer ${err['auto']['total']:,}",
             f"Gross revenue error (misclassified $/month, no offsetting): engine ${m['gross_dollar_error_per_month']['engine']:,}"
             f" -> reviewer ${m['gross_dollar_error_per_month']['auto']:,}",
             f"Offer error, sum of |error|: engine ${s['engine']['abs_offer_error_total']:,}"
             f" -> reviewer ${s['auto']['abs_offer_error_total']:,}",
             f"Wrong fund/decline decisions: engine {len(s['engine']['wrong_decisions'])}"
             f" {s['engine']['wrong_decisions']} -> reviewer {len(s['auto']['wrong_decisions'])}",
             f"Brief's offer rule, wrongly funded (truth offer is 0): engine {s['engine']['wrongly_funded']}"
             f" -> reviewer {s['auto']['wrongly_funded']}",
             f"Our rule (fund/decline/refer): wrongly funded {s['our_rule']['wrongly_funded']}, "
             f"wrongly declined {s['our_rule']['wrongly_declined']}, overfunded ${s['our_rule']['overfunded_usd']:,}, "
             f"underfunded ${s['our_rule']['underfunded_usd']:,}",
             f"  referred to an underwriter: {s['our_rule']['referred'] or 'none'}",
             f"Flags: {m['flags']} transactions, precision {m['flag_precision']:.1%}, "
             f"material errors caught {m['recall_material']:.1%}; status {dict(m['status_counts'])}",
             f"Auto-corrections that broke a correct label: {m['auto_corrections_that_broke_a_correct_label']}; "
             f"that made a materially right label wrong: {m['auto_corrections_made_materially_wrong']}; "
             f"still materially wrong after correction: {m['auto_corrections_still_materially_wrong']}",
             f"Hard negatives flagged: {hn['flagged']} of {hn['n']}",
             f"LLM spend recorded in the cache (USD): {spend()}",
             "", "Details: outputs/<model>/metrics.json, outputs/credit/report.md"]
    return "\n".join(rows)


def review_input(path: str, model_id: str, offline: bool, truth_path=None, assets=None, meta=None) -> None:
    out = OUT / "input" / Path(path).stem
    businesses = load(path, assets, meta)
    s = review.run(model_id, offline, path, out_dir=out, businesses=businesses)
    reviews = json.loads((out / "reviews.json").read_text())
    print(f"\n{s['transactions']} transactions | status {s['status_counts']} | "
          f"excluded pending {s['excluded_pending'] or 0} | LLM calls {s['llm_calls']}")
    if s["errors"]:
        print(f"{len(s['errors'])} chunk(s) not reviewed (engine label kept): {s['errors'][0]['error']}")
    for b in businesses:
        by_id = {t["transaction_id"]: t for t in b["transactions"]}
        flagged = [(tid, r) for tid, r in reviews.items()
                   if tid in by_id and r["status"] in ("corrected", "needs_review")]
        unreviewed = sum(reviews[tid]["status"] == "unreviewed" for tid in by_id)
        print(f"\n== {b['business_id']}: {len(flagged)} flagged transactions"
              + (f", {unreviewed} unreviewed (no LLM response; engine label kept)" if unreviewed else ""))
        groups = {}
        for tid, r in flagged:
            groups.setdefault(r["group_ref"], []).append((by_id[tid], r))
        for items in sorted(groups.values(), key=lambda it: -sum(abs(t["amount"]) for t, _ in it)):
            t, r = items[0]
            e, p = r["engine"], r["proposed"] or {}
            why = r.get("evidence_group") or r.get("evidence_business") or r.get("held") or ""
            total = sum(abs(x["amount"]) for x, _ in items)
            print(f"  {r['status']:12} {len(items):3} txns ${total:>10,.2f}  {t['original_description'][:40]:40} "
                  f"{e['group']} -> {p.get('group', '-')} | revenue {e['revenue']} -> {p.get('revenue', '-')} | "
                  f"conf {r['confidence']} | {r['reason']} [{why}]")
        labels = {"engine": label_all(b["transactions"]),
                  "reviewer": {tid: reviews[tid]["final"] for tid in by_id},
                  "accept_all": {tid: reviews[tid]["proposed"] or reviews[tid]["final"] for tid in by_id}}
        f = {name: features(b, lab) for name, lab in labels.items()}
        for name in ("engine", "reviewer"):
            x = f[name]
            print(f"  {name:8} monthly revenue ${x['monthly_revenue']:,} | revenue share {x['revenue_share']} | "
                  f"NSF {x['nsf_count']} | OD {x['overdraft_count']} | high-risk {x['high_risk_share']:.1%} | "
                  f"other funders ${x['other_funders_daily']:,.0f}/day | offer ${x['offer']:,} | {x['days']} days")
        neg = f["reviewer"]["negative_days"]
        d = decide(f["reviewer"], f["engine"], f["accept_all"], unreviewed)
        bal = "no asset report" if neg is None else f"{neg} negative days, average ${f['reviewer']['avg_daily_balance']:,}"
        print(f"  balance  {bal}")
        print(f"  decision {d['decision'].upper()} ${d['offer']:,}" + (f" | {'; '.join(d['reasons'])}" if d["reasons"] else ""))
    if truth_path:
        score_input(model_id, out, businesses, reviews, truth_path)
    print(f"\nFull output: {out}/reviews.json")


def score_input(model_id, out, businesses, reviews, truth_path) -> None:
    truth, notes = evaluate.read_truth(truth_path)
    truth, more = evaluate.complete_truth(businesses, truth)
    m = evaluate.evaluate(model_id, None, out, truth=truth, businesses=businesses)
    ba = simulate.before_after(businesses, truth, reviews)
    (out / "before_after.json").write_text(json.dumps(ba, indent=1))
    print("\n==== Scored against the truth file " + truth_path)
    for n in notes + more:
        print("  note: " + n)
    print(summary(model_id, m, ba))
    errors = evaluate.top_errors(businesses, truth, reviews)
    (out / "top_errors.json").write_text(json.dumps(errors, indent=1))
    print("\nCostliest errors left after review (engine -> proposed -> final | truth):")
    for e in errors:
        print(f"  {e['business']} ${e['usd']:>10,.2f} {e['n']:3} txns  {e['description'][:38]:38} "
              f"{e['engine']} -> {e['proposed'] or '-'} -> {e['final']} | truth {e['truth']} | "
              f"{e['outcome']}, {e['effect']} | {e['reason']}")


def main():
    ap = argparse.ArgumentParser(description='One command for the whole pipeline.')
    ap.add_argument("--use-cache", action="store_true",
                    help=f"replay the committed cache only (model {CACHED_MODEL} unless --model)")
    ap.add_argument("--model", help="model id; default from MODEL_ID / available credentials")
    ap.add_argument("--input", help="transactions to review: a /transactions/get or /transactions/sync "
                                    "response, a list of transactions, or a folder with businesses.json")
    ap.add_argument("--truth", help="with --input: correct labels to score against (see README)")
    ap.add_argument("--assets", help="with --input FILE: its /asset_report/get response (daily balances)")
    ap.add_argument("--owner", help="with --input FILE: owner name on the application")
    ap.add_argument("--name", help="with --input FILE: business name on the application")
    ap.add_argument("--data", help="a generated dataset folder with truth.json (default data/generated)")
    ap.add_argument("--trials", type=int, default=100, help="Monte Carlo trials for the mislabel simulation")
    a = ap.parse_args()
    model_id = a.model or (CACHED_MODEL if a.use_cache else default_model())

    if a.input:
        meta = {k: v for k, v in (("owner_name", a.owner), ("name", a.name)) if v}
        review_input(a.input, model_id, a.use_cache, a.truth, a.assets, meta)
        return
    out = OUT / Path(a.data).name / model_slug(model_id) if a.data else None
    print(f"1/3 reviewing {a.data or 'data/generated'} with {model_id}{' (cache only)' if a.use_cache else ''} ...",
          file=sys.stderr)
    s = review.run(model_id, a.use_cache, a.data, out_dir=out)
    if s["errors"]:
        print(f"    {len(s['errors'])} chunk(s) not reviewed (engine label kept): {s['errors'][0]['error']}",
              file=sys.stderr)
    print("2/3 evaluating against the synthetic truth ...", file=sys.stderr)
    m = evaluate.evaluate(model_id, a.data, out)
    print("3/3 credit impact and mislabel simulation ...", file=sys.stderr)
    ba, _, _ = simulate.run(model_id, a.trials, a.data, out,
                            OUT / Path(a.data).name / "credit" if a.data else None)
    print(summary(model_id, m, ba))


if __name__ == "__main__":
    main()
