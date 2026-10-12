import json
import re
from collections import Counter
from pathlib import Path

from data.load import load, load_truth
from labels import NONE, is_revenue

KEYWORDS = {
    "nsf": ["NSF", "N.S.F.", "INSUFFICIENT FUNDS", "NON-SUFFICIENT"],
    "overdraft": ["OVERDRAFT", "OD FEE", "OD CHARGE"],
    "hr_garnishment": ["GARNISH", "LEVY", "WAGE ORDER"],
    "hr_bankruptcy": ["BANKRUPTCY", "CHAPTER 13", "CHAPTER 7", "CH. 13"],
    "hr_debt_settlement": ["DEBT RELIEF", "DEBT SETTLEMENT", "NATIONAL DEBT"],
    "hr_gambling": ["DRAFTKINGS", "FANDUEL", "CASINO", "BETMGM", "LOTTERY"],
    "hr_other": ["PAWN", "PAYDAY", "BAIL BOND"],
    "active_advance": ["FUNDING", "ADVANCE", "MCA", "MERCHANT CAP", "LIBERTAS", "YELLOWSTONE", "RAPID FIN"],
    "ucc": ["UCC", "EQUIP", "LEASE", "LOAN PMT", "FINANCIAL SVCS"],
    "internal_transfer": ["TRANSFER", "XFER", "TRF FROM", "BOOK TRANSFER"],
    "not_revenue": ["REFUND", "TAX REF", "REVERSAL", "RETURN", "INTEREST", "LOAN", "EIDL"],
    "auto_deposit": ["ZELLE", "VENMO", "CASH APP", "AUTODEPOSIT"],
    "revenue_verification": ["SQUARE", "SQ *", "STRIPE", "SHOPIFY", "PAYPAL", "DOORDASH", "UBER EATS",
                             "GRUBHUB", "MERCH DEP"],
}
PERSONAL = ["NETFLIX", "SPOTIFY", "HULU", "VENMO", "PLANET FITNESS", "DISNEY PLUS", "APPLE.COM/BILL",
            "DRAFTKINGS", "FANDUEL"]

DATA = Path(__file__).parent.parent / "data" / "generated"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", text.upper())).strip()


def _hits(norm: str, keywords: list[str]) -> list[str]:
    return [kw for kw in keywords if re.search(r"(?<![A-Z0-9])" + re.escape(kw), norm)]


def label(txn: dict) -> dict:
    norm = normalize(txn["original_description"])
    matches = {g: h for g, kws in KEYWORDS.items() if (h := _hits(norm, kws))}
    group = next(iter(matches), NONE)
    is_business = not _hits(norm, PERSONAL)
    return {
        "group": group,
        "is_business": is_business,
        "revenue": is_revenue(txn["amount"], group, is_business),
        "matched": matches,
    }


def label_all(transactions: list[dict]) -> dict[str, dict]:
    return {t["transaction_id"]: label(t) for t in transactions}


def main():
    truth = load_truth()
    txns = [t for b in load() for t in b["transactions"]]
    labels = label_all(txns)
    (DATA / "engine_labels.json").write_text(json.dumps(labels, indent=1))

    wrong_group, wrong_biz, wrong_rev, by_case = 0, 0, 0, Counter()
    for t in txns:
        e, tr = labels[t["transaction_id"]], truth[t["transaction_id"]]
        tr_rev = is_revenue(t["amount"], tr["group"], tr["is_business"])
        bad = False
        if e["group"] != tr["group"]:
            wrong_group += 1; bad = True
        if e["is_business"] != tr["is_business"]:
            wrong_biz += 1; bad = True
        if e["revenue"] != tr_rev:
            wrong_rev += 1
        if bad:
            by_case[(tr["case"], tr["group"], e["group"])] += 1
    n = len(txns)
    print(f"{n} transactions | wrong group {wrong_group} ({wrong_group/n:.1%}) | "
          f"wrong business flag {wrong_biz} | wrong revenue {wrong_rev}")
    print("\nerrors by case (truth -> engine):")
    for (case, tg, eg), c in by_case.most_common():
        print(f"  {c:4d}  {case:40s} {tg:22s} -> {eg}")


if __name__ == "__main__":
    main()
