from credit.features import NSF_LIMIT, offer_rule

MIN_DAYS = 60
NEG_DAY_SHARE = 0.10
MAX_BURDEN = 0.25


def _rule_decline(f: dict) -> bool:
    return f["nsf_per_90"] > NSF_LIMIT


def decide(f_auto: dict, f_engine: dict, f_accept: dict, unreviewed: int = 0) -> dict:
    reasons = []
    if unreviewed:
        reasons.append(f"review incomplete: {unreviewed} transactions kept the engine label")
    if f_auto.get("negative_days") is None:
        reasons.append("no daily balances to cross-check the labels")
    if f_auto["days"] < MIN_DAYS:
        reasons.append(f"only {f_auto['days']} days of history")
    if _rule_decline(f_auto):
        return {"decision": "decline", "offer": 0,
                "reasons": [f"{f_auto['nsf_per_90']} NSFs per 90 days > {NSF_LIMIT}"]}
    neg = f_auto.get("negative_days")
    if neg is not None and neg > NEG_DAY_SHARE * f_auto["days"]:
        reasons.append(f"{neg} negative-balance days with {f_auto['nsf_count']} NSFs labeled: "
                       f"the balance shows stress the labels do not explain")
    burden = f_auto.get("repayment_burden")
    if burden is not None and burden > MAX_BURDEN:
        reasons.append(f"other funders already take {burden:.0%} of monthly revenue")
    if any(_rule_decline(f) for f in (f_engine, f_accept)):
        reasons.append("the NSF decision changes with labels still in doubt")
    offers = [offer_rule(f["monthly_revenue"], f["other_funders_daily"], 0) for f in (f_auto, f_accept)]
    offer = round(min(offers))
    if reasons:
        return {"decision": "refer", "offer": offer, "reasons": reasons}
    if offer <= 0:
        return {"decision": "decline", "offer": 0, "reasons": ["other funders' payments exceed the offer"]}
    return {"decision": "fund", "offer": offer, "reasons": []}
