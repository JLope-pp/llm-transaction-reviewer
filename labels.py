GROUPS = [
    "not_revenue",
    "revenue_verification",
    "nsf",
    "overdraft",
    "internal_transfer",
    "ucc",
    "active_advance",
    "auto_deposit",
    "hr_gambling",
    "hr_bankruptcy",
    "hr_debt_settlement",
    "hr_garnishment",
    "hr_other",
]
NONE = "none"
ALL_GROUPS = GROUPS + [NONE]

HIGH_RISK = {g for g in GROUPS if g.startswith("hr_")}

EXCLUDING = {
    "not_revenue", "nsf", "overdraft", "internal_transfer", "ucc", "active_advance",
} | HIGH_RISK


def is_credit(amount: float) -> bool:
    return amount < 0


def is_revenue(amount: float, group: str, is_business: bool) -> bool:
    return is_credit(amount) and is_business and group not in EXCLUDING


CREDIT_ONLY = {"not_revenue", "revenue_verification", "auto_deposit"}

FEATURE_GROUPS = {"nsf", "overdraft", "active_advance"} | HIGH_RISK


def material_change(amount: float, a: dict, b: dict) -> bool:
    if is_revenue(amount, a["group"], a["is_business"]) != is_revenue(amount, b["group"], b["is_business"]):
        return True
    return a["group"] != b["group"] and (a["group"] in FEATURE_GROUPS or b["group"] in FEATURE_GROUPS)
