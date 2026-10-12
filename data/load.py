import json
from pathlib import Path

GENERATED = Path(__file__).parent / "generated"


def _normalize(t: dict) -> dict:
    t = dict(t)
    t["amount"] = float(t["amount"])
    t["payment_meta"] = t.get("payment_meta") or {}
    t["counterparties"] = [{"name": c.get("name"), "type": c.get("type"), **c}
                           for c in t.get("counterparties") or []]
    t["original_description"] = t.get("original_description") or t.get("name") or t.get("merchant_name") or ""
    t["payment_channel"] = t.get("payment_channel") or "other"
    t.setdefault("account_id", "account")
    pfc = t.get("personal_finance_category")
    if pfc:
        t["personal_finance_category"] = {"confidence_level": "UNKNOWN", **pfc,
                                          "detailed": pfc.get("detailed") or pfc.get("primary")}
    else:
        t["personal_finance_category"] = None
    return t


def _posted(transactions: list[dict]) -> list[dict]:
    return [_normalize(t) for t in transactions if not t.get("pending")]


def transactions_response(obj) -> dict:
    if isinstance(obj, list):
        return {"accounts": [], "transactions": obj}
    if "transactions" in obj:
        return obj
    if "added" in obj:
        by_id = {t["transaction_id"]: t for t in obj.get("added", [])}
        by_id.update({t["transaction_id"]: t for t in obj.get("modified", [])})
        for r in obj.get("removed", []):
            by_id.pop(r["transaction_id"], None)
        return {"accounts": obj.get("accounts", []), "transactions": list(by_id.values())}
    raise ValueError("expected a /transactions/get or /transactions/sync response, or a list of transactions")


def _business(biz_id, meta, tx, assets=None):
    balances = None
    if assets:
        report = assets.get("report", assets)
        balances = {a["account_id"]: a.get("historical_balances", [])
                    for item in report["items"] for a in item["accounts"]}
    tx = transactions_response(tx)
    return {
        "business_id": biz_id,
        "meta": meta,
        "accounts": tx.get("accounts") or [],
        "transactions": _posted(tx["transactions"]),
        "excluded_pending": sum(bool(t.get("pending")) for t in tx["transactions"]),
        "historical_balances": balances,
    }


def load(path: str | Path = GENERATED, assets: str | Path | None = None, meta: dict | None = None) -> list[dict]:
    path = Path(path)
    if path.is_file():
        tx = json.loads(path.read_text())
        report = json.loads(Path(assets).read_text()) if assets else None
        return [_business(path.stem, meta or {}, tx, report)]
    out = []
    for m in json.loads((path / "businesses.json").read_text()):
        tx = json.loads((path / m["transactions_file"]).read_text())
        assets_path = path / m.get("assets_file", "")
        report = json.loads(assets_path.read_text()) if assets_path.is_file() else None
        out.append(_business(m["business_id"], m, tx, report))
    return out


def load_truth(path: str | Path = GENERATED) -> dict:
    return json.loads((Path(path) / "truth.json").read_text())
