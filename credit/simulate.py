import argparse
import json
import random
import statistics
from pathlib import Path

from credit.decision import decide
from credit.features import features, funder
from data.load import load, load_truth
from engine.keywords import label_all, normalize
from labels import ALL_GROUPS, is_credit, is_revenue
from reviewer.llm import default_model, model_slug

OUT = Path(__file__).parent.parent / "outputs" / "credit"
RATES = (0.02, 0.05, 0.10)
SEED = 20261010


def before_after(businesses, truth, reviews) -> dict:
    rows = {}
    for b in businesses:
        engine = label_all(b["transactions"])
        ids = [t["transaction_id"] for t in b["transactions"]]
        auto = {i: reviews[i]["final"] for i in ids}
        accept = {i: reviews[i]["proposed"] or reviews[i]["final"] for i in ids}
        rows[b["business_id"]] = {name: features(b, lab) for name, lab in
                                  (("truth", truth), ("engine", engine), ("auto", auto), ("accept_all", accept))}
        v = rows[b["business_id"]]
        v["our_rule"] = decide(v["auto"], v["engine"], v["accept_all"],
                               sum(reviews[i]["status"] == "unreviewed" for i in ids))
    summary = {"our_rule": our_rule_summary(rows)}
    for name in ("engine", "auto", "accept_all"):
        wrong = [k for k, v in rows.items() if (v[name]["offer"] > 0) != (v["truth"]["offer"] > 0)]
        summary[name] = {
            "abs_offer_error_total": sum(abs(v[name]["offer"] - v["truth"]["offer"]) for v in rows.values()),
            "offer_overstated_total": sum(max(0, v[name]["offer"] - v["truth"]["offer"]) for v in rows.values()),
            "wrong_decisions": wrong,
            "wrongly_funded": [k for k, v in rows.items() if v[name]["offer"] > 0 and v["truth"]["offer"] == 0],
        }
    return {"by_business": rows, "summary": summary}


def our_rule_summary(rows: dict) -> dict:
    d = {k: v["our_rule"] for k, v in rows.items()}
    return {
        "funded": [k for k, x in d.items() if x["decision"] == "fund"],
        "declined": [k for k, x in d.items() if x["decision"] == "decline"],
        "referred": {k: x["reasons"] for k, x in d.items() if x["decision"] == "refer"},
        "wrongly_funded": [k for k, x in d.items() if x["decision"] == "fund" and rows[k]["truth"]["offer"] == 0],
        "wrongly_declined": [k for k, x in d.items() if x["decision"] == "decline" and rows[k]["truth"]["offer"] > 0],
        "overfunded_usd": sum(max(0, x["offer"] - rows[k]["truth"]["offer"]) for k, x in d.items()
                              if x["decision"] == "fund"),
        "underfunded_usd": sum(max(0, rows[k]["truth"]["offer"] - x["offer"]) for k, x in d.items()
                               if x["decision"] == "fund"),
    }


def _eligible(kind, t, lab):
    amt, g, biz = t["amount"], lab["group"], lab["is_business"]
    rev = is_revenue(amt, g, biz)
    return {
        "missed_revenue": rev,
        "false_revenue": is_credit(amt) and not rev,
        "false_advance": not is_credit(amt) and g == "none",
        "missed_advance": not is_credit(amt) and g == "active_advance",
        "missed_nsf": g == "nsf",
        "false_nsf": g == "overdraft",
        "immaterial": rev or (not is_credit(amt) and g == "none"),
        "uniform": True,
    }[kind]


def _corrupt(kind, t, lab, rng):
    amt = t["amount"]
    if kind == "missed_revenue":
        return {"group": "not_revenue", "is_business": True}
    if kind == "false_revenue":
        return {"group": "none", "is_business": True}
    if kind in ("false_advance",):
        return {"group": "active_advance", "is_business": True}
    if kind in ("missed_advance", "missed_nsf"):
        return {"group": "none", "is_business": lab["is_business"]}
    if kind == "false_nsf":
        return {"group": "nsf", "is_business": True}
    if kind == "immaterial":
        if is_credit(amt):
            return {"group": rng.choice([g for g in ("none", "revenue_verification", "auto_deposit")
                                         if g != lab["group"]]), "is_business": True}
        return {"group": "none", "is_business": not lab["is_business"]}
    return {"group": rng.choice([g for g in ALL_GROUPS if g != lab["group"]]), "is_business": lab["is_business"]}


KINDS = ("missed_revenue", "false_revenue", "false_advance", "missed_advance",
         "missed_nsf", "false_nsf", "immaterial", "uniform")


def counterparty(t: dict) -> str:
    return normalize(t["payment_meta"].get("payer") or "") or funder(t)


def simulate(businesses, truth, trials: int, unit: str) -> dict:
    base = {b["business_id"]: features(b, truth) for b in businesses}
    out = {}
    for kind in KINDS:
        for rate in RATES:
            rng = random.Random(f"{SEED}-{unit}-{kind}-{rate}")
            d_offer, d_abs, d_rev, flips, d_share, d_nsf, d_hr, d_daily = [], [], [], 0, [], [], [], []
            hit_abs, hit_flips = [], 0
            n = 0
            for _ in range(trials):
                for b in businesses:
                    lab, hit = dict(truth), {}
                    for t in b["transactions"]:
                        tid = t["transaction_id"]
                        if not _eligible(kind, t, truth[tid]):
                            continue
                        if unit == "counterparty":
                            cp = counterparty(t)
                            if cp not in hit:
                                hit[cp] = rng.random() < rate
                            wrong = hit[cp]
                        else:
                            wrong = rng.random() < rate
                        if wrong:
                            lab[tid] = _corrupt(kind, t, truth[tid], rng)
                    f, f0 = features(b, lab), base[b["business_id"]]
                    d_offer.append(f["offer"] - f0["offer"])
                    d_abs.append(abs(f["offer"] - f0["offer"]))
                    d_rev.append(f["monthly_revenue"] - f0["monthly_revenue"])
                    d_share.append((f["revenue_share"] or 0) - (f0["revenue_share"] or 0))
                    d_nsf.append(f["nsf_count"] - f0["nsf_count"])
                    d_hr.append(f["high_risk_share"] - f0["high_risk_share"])
                    d_daily.append(f["other_funders_daily"] - f0["other_funders_daily"])
                    flip = (f["offer"] > 0) != (f0["offer"] > 0)
                    flips += flip
                    if lab != truth:
                        hit_abs.append(abs(f["offer"] - f0["offer"]))
                        hit_flips += flip
                    n += 1
            out[f"{unit}:{kind}@{rate:.0%}"] = {
                "unit": unit, "kind": kind, "rate": rate,
                "mean_offer_change": round(statistics.mean(d_offer)),
                "mean_abs_offer_change": round(statistics.mean(d_abs)),
                "mean_monthly_revenue_change": round(statistics.mean(d_rev)),
                "mean_revenue_share_change_pp": round(100 * statistics.mean(d_share), 2),
                "mean_nsf_change": round(statistics.mean(d_nsf), 2),
                "mean_high_risk_share_change_pp": round(100 * statistics.mean(d_hr), 2),
                "mean_daily_payment_change": round(statistics.mean(d_daily), 2),
                "decision_flip_rate": round(flips / n, 3),
                "share_hit": round(len(hit_abs) / n, 3),
                "abs_offer_change_when_hit": round(statistics.mean(hit_abs)) if hit_abs else 0,
                "flip_rate_when_hit": round(hit_flips / len(hit_abs), 3) if hit_abs else 0,
            }
    return out


def report(ba: dict, sim: dict, model_id: str) -> str:
    lines = [f"# Credit impact (reviewer: {model_id})", "",
             "## Before / after, per business (MEASURED against synthetic truth)", "",
             "| Biz | Labels | Monthly rev | Rev % deposits | NSF | OD | High-risk % debits | Other funders $/day | Offer |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for biz, v in ba["by_business"].items():
        for name in ("truth", "engine", "auto"):
            f = v[name]
            lines.append(f"| {biz} | {name} | {f['monthly_revenue']:,} | {f['revenue_share']:.1%} | {f['nsf_count']} | "
                         f"{f['overdraft_count']} | {f['high_risk_share']:.1%} | {f['other_funders_daily']:,.0f} | "
                         f"{f['offer']:,} |")
    lines += ["", "| Labels | Abs offer error (sum) | Overstated offers (sum) | Wrong fund/decline decisions |",
              "|---|---:|---:|---|"]
    for name, s in ((k, v) for k, v in ba["summary"].items() if k != "our_rule"):
        lines.append(f"| {name} | ${s['abs_offer_error_total']:,} | ${s['offer_overstated_total']:,} | "
                     f"{len(s['wrong_decisions'])} {s['wrong_decisions']} |")
    o = ba["summary"]["our_rule"]
    lines += ["", "## Our rule: fund / decline / refer (reviewer labels + balance + doubt)", "",
              "| Biz | Decision | Offer | Truth offer (brief's rule) | Reasons |", "|---|---|---:|---:|---|"]
    for biz, v in ba["by_business"].items():
        r = v["our_rule"]
        lines.append(f"| {biz} | {r['decision']} | {r['offer']:,} | {v['truth']['offer']:,} | {'; '.join(r['reasons'])} |")
    lines += ["", f"Wrongly funded: {o['wrongly_funded'] or 'none'}. Wrongly declined: {o['wrongly_declined'] or 'none'}. "
              f"Overfunded ${o['overfunded_usd']:,}, underfunded ${o['underfunded_usd']:,} (funded only). "
              f"Referred: {list(o['referred']) or 'none'}."]
    lines += ["", "## Mislabel simulation from the true labels (ESTIMATED, Monte Carlo)", "",
              "Rate = share of the transactions (unit txn) or counterparties (unit counterparty) eligible "
              "for that error type. Means per business and trial.", "",
              "| Unit | Error type | Rate | Offer Δ | |Offer Δ| | Monthly rev Δ | Rev share Δ pp | NSF Δ | High-risk Δ pp | Funders $/day Δ | Decision flips | Hit | |Offer Δ| when hit | Flips when hit |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for s in sim.values():
        lines.append(f"| {s['unit']} | {s['kind']} | {s['rate']:.0%} | {s['mean_offer_change']:+,} | {s['mean_abs_offer_change']:,} | "
                     f"{s['mean_monthly_revenue_change']:+,} | {s['mean_revenue_share_change_pp']:+.2f} | "
                     f"{s['mean_nsf_change']:+.2f} | {s['mean_high_risk_share_change_pp']:+.2f} | "
                     f"{s['mean_daily_payment_change']:+,.0f} | {s['decision_flip_rate']:.1%} | {s['share_hit']:.0%} | "
                     f"{s['abs_offer_change_when_hit']:,} | {s['flip_rate_when_hit']:.1%} |")
    return "\n".join(lines) + "\n"


def run(model_id: str, trials: int = 100, data=None, reviews_dir=None, out_dir=None) -> tuple[dict, dict, str]:
    businesses = load(data) if data else load()
    truth = load_truth(data) if data else load_truth()
    reviews_dir = Path(reviews_dir) if reviews_dir else OUT.parent / model_slug(model_id)
    out = Path(out_dir) if out_dir else OUT
    reviews = json.loads((reviews_dir / "reviews.json").read_text())
    ba = before_after(businesses, truth, reviews)
    sim = {**simulate(businesses, truth, trials, "txn"),
           **simulate(businesses, truth, trials, "counterparty")}
    out.mkdir(parents=True, exist_ok=True)
    (out / "before_after.json").write_text(json.dumps(ba, indent=1))
    (out / "simulation.json").write_text(json.dumps(sim, indent=1))
    text = report(ba, sim, model_id)
    (out / "report.md").write_text(text)
    return ba, sim, text


def main():
    ap = argparse.ArgumentParser(description='Part 2: what the labels are worth to a funding decision.')
    ap.add_argument("--model", default=default_model())
    ap.add_argument("--trials", type=int, default=100)
    a = ap.parse_args()
    print(run(a.model, a.trials)[2])


if __name__ == "__main__":
    main()
