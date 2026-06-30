# ============================================
# Database - JSON file storage
# ============================================
import json
import os
import uuid
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def _load():
    if not os.path.exists(DB_FILE):
        return {"transactions": []}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def _save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def add_transaction(txn_type, phone_number, amount, reference_id, status="PENDING"):
    data = _load()
    txn = {
        "id": str(uuid.uuid4())[:8],
        "type": txn_type,
        "phone_number": phone_number,
        "amount": amount,
        "reference_id": reference_id,
        "status": status,
        "note": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    data["transactions"].insert(0, txn)
    _save(data)
    return txn


def update_note(transaction_id, note):
    data = _load()
    for txn in data["transactions"]:
        if txn["id"] == transaction_id:
            txn["note"] = note
            txn["updated_at"] = datetime.now().isoformat()
            _save(data)
            return txn
    return None


def update_status(transaction_id, status):
    data = _load()
    for txn in data["transactions"]:
        if txn["id"] == transaction_id:
            txn["status"] = status
            txn["updated_at"] = datetime.now().isoformat()
            _save(data)
            return txn
    return None


def get_all_transactions():
    return _load()["transactions"]


def get_transaction(transaction_id):
    for txn in _load()["transactions"]:
        if txn["id"] == transaction_id:
            return txn
    return None


def get_stats():
    txns = get_all_transactions()
    return {
        "total_transactions": len(txns),
        "total_sent": sum(t["amount"] for t in txns if t["type"] == "SEND" and t["status"] == "SUCCESSFUL"),
        "total_received": sum(t["amount"] for t in txns if t["type"] == "REQUEST" and t["status"] == "SUCCESSFUL"),
        "total_pending": sum(t["amount"] for t in txns if t["status"] == "PENDING"),
        "with_notes": sum(1 for t in txns if t.get("note")),
        "without_notes": sum(1 for t in txns if not t.get("note")),
    }
