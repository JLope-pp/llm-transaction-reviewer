from datetime import date, timedelta

from engine.keywords import normalize
from labels import HIGH_RISK, is_credit, is_revenue

DAYS_PER_MONTH = 30.4
ACTIVE_WINDOW = 30
NSF_LIMIT = 5


def offer_rule(monthly_revenue: float, daily_payments: float, nsf_count: int) -> float:
    if nsf_count > NSF_LIMIT:
        return 0.0
    return max(0.0, 1.2 * monthly_revenue - 20 * daily_payments)


def coverage_days(business: dict) -> int:
    balances = business.get("historical_balances")
    if balances:
        return max(len({h["date"] for h in hs}) for hs in balances.values())
    dates = [date.fromisoformat(t["date"]) for t in business["transactions"]]
    return (max(dates) - min(dates)).days + 1


def funder(t: dict) -> str:
    pm = t["payment_meta"]
    who = pm.get("payee") or t.get("merchant_name") or (t["counterparties"][0]["name"] if t["counterparties"] else "")
    return normalize(who) or " ".join(normalize(t["original_description"]).split()[:2])


def _business_days(start: date, end: date) -> int:
    return sum((start + timedelta(d)).weekday() < 5 for d in range((end - start).days + 1))


def features(business: dict, labels: dict) -> dict:
    txns = business["transactions"]
    days = coverage_days(business)
    end = max(date.fromisoformat(t["date"]) for t in txns)
    start = end - timedelta(ACTIVE_WINDOW - 1)
    deposits = revenue = debits = high_risk = 0.0
    nsf = od = 0
    paid = {}
    for t in txns:
        lab = labels[t["transaction_id"]]
        amt, group = t["amount"], lab["group"]
        if is_credit(amt):
            deposits += -amt
            if is_revenue(amt, group, lab["is_business"]):
                revenue += -amt
        else:
            debits += amt
            if group in HIGH_RISK:
                high_risk += amt
            if group == "active_advance" and date.fromisoformat(t["date"]) >= start:
                paid[funder(t)] = paid.get(funder(t), 0.0) + amt
        nsf += group == "nsf"
        od += group == "overdraft"
    bdays = _business_days(start, end)
    hb = business.get("historical_balances")
    balances = [h["current"] for h in next(iter(hb.values()))] if hb else None
    daily = {f: round(v / bdays, 2) for f, v in paid.items()}
    monthly = revenue * DAYS_PER_MONTH / days
    daily_total = sum(daily.values())
    return {
        "days": days,
        "monthly_revenue": round(monthly),
        "revenue_share": round(revenue / deposits, 3) if deposits else None,
        "nsf_count": nsf,
        "nsf_per_90": round(nsf * 90 / days, 1),
        "negative_days": sum(b < 0 for b in balances) if balances is not None else None,
        "avg_daily_balance": round(sum(balances) / len(balances)) if balances else None,
        "overdraft_count": od,
        "high_risk_share": round(high_risk / debits, 4) if debits else 0.0,
        "other_funders_daily": round(daily_total, 2),
        "funders": daily,
        "offer": round(offer_rule(monthly, daily_total, nsf)),
        "repayment_burden": round(daily_total * 21.7 / monthly, 3) if monthly > 0 else None,
    }
