from labels import ALL_GROUPS, FEATURE_GROUPS

ORDINARY_SPEND = ("FOOD_AND_DRINK", "GENERAL_MERCHANDISE", "GENERAL_SERVICES", "HOME_IMPROVEMENT",
                  "MEDICAL", "PERSONAL_CARE", "RENT_AND_UTILITIES", "TRANSPORTATION", "TRAVEL",
                  "ENTERTAINMENT_TV_AND_MOVIES", "ENTERTAINMENT_MUSIC_AND_AUDIO",
                  "GOVERNMENT_AND_NON_PROFIT_TAX_PAYMENT")
NO_PLAID_CATEGORY = {"hr_bankruptcy", "hr_debt_settlement", "hr_garnishment", "hr_other"}
REVENUE_GROUPS = {"none", "revenue_verification", "auto_deposit"}
PROCESSORS = {"payment_terminal", "marketplace", "payment_app"}


def _has_fact(group: dict, text: str) -> bool:
    return any(text in f for f in group.get("facts", []))


def supports(group: dict, proposed: str) -> str | None:
    if group.get("_returned"):
        return "returned debit while the balance was negative" if proposed == "nsf" else None
    pfc = group.get("_pfc") or ""
    cp = group.get("_cp_type")
    credit = group["direction"] == "CREDIT"
    link = _has_fact(group, "same counterparty also has")
    if proposed == "active_advance":
        if link:
            return "funding/repayment link"
        if pfc.startswith(("LOAN_PAYMENTS_CASH_ADVANCES", "LOAN_DISBURSEMENTS_CASH_ADVANCES")):
            return f"Plaid {pfc}"
    elif proposed == "ucc":
        if not credit and pfc.startswith("LOAN_PAYMENTS_") and "CASH_ADVANCES" not in pfc:
            return f"Plaid {pfc}"
    elif proposed == "revenue_verification":
        if credit and cp in PROCESSORS and not pfc.startswith("LOAN_"):
            return f"Plaid counterparty type {cp}"
    elif proposed == "auto_deposit":
        if credit and (pfc == "TRANSFER_IN_TRANSFER_IN_FROM_APPS" or cp == "payment_app"):
            return f"Plaid {pfc or cp}"
    elif proposed == "internal_transfer":
        if _has_fact(group, "payer matches the owner"):
            return "payer matches the owner"
        if pfc in ("TRANSFER_IN_ACCOUNT_TRANSFER", "TRANSFER_OUT_ACCOUNT_TRANSFER", "TRANSFER_OUT_SAVINGS") \
                and cp not in PROCESSORS:
            return f"Plaid {pfc}"
    elif proposed == "not_revenue":
        if credit and pfc.startswith(("LOAN_DISBURSEMENTS_", "INCOME_INTEREST", "INCOME_TAX_REFUND")):
            return f"Plaid {pfc}"
    elif proposed == "nsf":
        if pfc == "BANK_FEES_INSUFFICIENT_FUNDS":
            return f"Plaid {pfc}"
        if credit and any(f" {code} " in f" {d} " for d in group["descriptions"] for code in ("R01", "R09")):
            return "NACHA return code"
    elif proposed == "overdraft":
        if pfc == "BANK_FEES_OVERDRAFT_FEES":
            return f"Plaid {pfc}"
    elif proposed == "hr_gambling":
        if pfc == "ENTERTAINMENT_CASINOS_AND_GAMBLING":
            return f"Plaid {pfc}"
    elif proposed == "hr_other":
        if pfc.startswith(("LOAN_PAYMENTS_PERSONAL_LOAN", "LOAN_DISBURSEMENTS_PAYDAY")):
            return f"Plaid {pfc}"
    elif proposed == "none":
        if group["engine"]["group"] in NO_PLAID_CATEGORY:
            return None
        if not credit and pfc.startswith(ORDINARY_SPEND):
            return f"Plaid {pfc}"
        if credit and pfc in ("INCOME_OTHER", "TRANSFER_IN_DEPOSIT") and cp not in ("financial_institution",):
            return f"Plaid {pfc}"
    return None


PERSONAL_SPEND = ("ENTERTAINMENT_TV_AND_MOVIES", "ENTERTAINMENT_MUSIC_AND_AUDIO", "ENTERTAINMENT_CASINOS_AND_GAMBLING",
                  "PERSONAL_CARE_GYMS_AND_FITNESS_CENTERS", "LOAN_PAYMENTS_PERSONAL_LOAN_PAYMENT")


def supports_business(group: dict, is_business: bool) -> str | None:
    pfc = group.get("_pfc") or ""
    if not is_business:
        if pfc.startswith(PERSONAL_SPEND):
            return f"Plaid {pfc}"
        if _has_fact(group, "payer matches the owner"):
            return "payer matches the owner"
        return None
    if group["direction"] == "CREDIT":
        if group.get("_holder") == "business" and group.get("_names_business"):
            return "business account and bank descriptor names the business"
        return None
    if pfc.startswith(ORDINARY_SPEND) and not pfc.startswith(PERSONAL_SPEND):
        return f"Plaid {pfc}"
    return None


def plaid_contradiction(group: dict) -> list[str]:
    engine = group["engine"]["group"]
    if engine != "nsf" and supports(group, "nsf"):
        return ["nsf"]
    if (group["direction"] == "CREDIT" and engine in REVENUE_GROUPS
            and _has_fact(group, "same counterparty also has")):
        return ["active_advance"]
    if supports(group, engine):
        return []
    return [g for g in ALL_GROUPS if g != engine and supports(group, g)
            and (g != "none" or engine in FEATURE_GROUPS)]
