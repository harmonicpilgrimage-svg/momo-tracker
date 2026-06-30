# ============================================
# MoMo Tracker - Main Application
# ============================================
from flask import Flask, render_template, request, jsonify
from config import SECRET_KEY, DEBUG, MOMO_PHONE_NUMBER
from momo_api import send_money, request_payment, check_transaction_status, get_balance
from database import (
    add_transaction, update_note, update_status,
    get_all_transactions, get_transaction, get_stats,
)

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ============================================
# PAGES
# ============================================
@app.route("/")
def index():
    return render_template(
        "index.html",
        transactions=get_all_transactions(),
        stats=get_stats(),
        my_number=MOMO_PHONE_NUMBER,
    )


# ============================================
# API: Send Money
# ============================================
@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.get_json()
    phone = _clean_phone(data.get("phone", ""))
    amount = data.get("amount")
    note = data.get("note", "").strip()

    if not phone or len(phone) != 12:
        return jsonify({"success": False, "error": "Phone must be 12 digits (250XXXXXXXXX)"}), 400
    if not amount or not str(amount).isdigit() or int(amount) <= 0:
        return jsonify({"success": False, "error": "Enter a valid amount"}), 400
    amount = int(amount)

    result = send_money(phone, amount, payer_message=note)
    if not result["success"]:
        return jsonify(result), 500

    txn = add_transaction("SEND", phone, amount, result["reference_id"])
    if note:
        update_note(txn["id"], note)

    return jsonify({
        "success": True,
        "message": result["message"],
        "transaction_id": txn["id"],
        "reference_id": result["reference_id"],
    })


# ============================================
# API: Request Payment
# ============================================
@app.route("/api/request", methods=["POST"])
def api_request():
    data = request.get_json()
    phone = _clean_phone(data.get("phone", ""))
    amount = data.get("amount")
    note = data.get("note", "").strip()

    if not phone or len(phone) != 12:
        return jsonify({"success": False, "error": "Phone must be 12 digits (250XXXXXXXXX)"}), 400
    if not amount or not str(amount).isdigit() or int(amount) <= 0:
        return jsonify({"success": False, "error": "Enter a valid amount"}), 400
    amount = int(amount)

    result = request_payment(phone, amount, note=note)
    if not result["success"]:
        return jsonify(result), 500

    txn = add_transaction("REQUEST", phone, amount, result["reference_id"])
    if note:
        update_note(txn["id"], note)

    return jsonify({
        "success": True,
        "message": result["message"],
        "transaction_id": txn["id"],
        "reference_id": result["reference_id"],
    })


# ============================================
# API: Add/Update Note
# ============================================
@app.route("/api/transaction/<txn_id>/note", methods=["POST"])
def api_add_note(txn_id):
    data = request.get_json()
    note = data.get("note", "").strip()
    if not note:
        return jsonify({"success": False, "error": "Note cannot be empty"}), 400
    txn = update_note(txn_id, note)
    if txn:
        return jsonify({"success": True, "transaction": txn})
    return jsonify({"success": False, "error": "Transaction not found"}), 404


# ============================================
# API: Check Transaction Status
# ============================================
@app.route("/api/transaction/<txn_id>/check", methods=["POST"])
def api_check_status(txn_id):
    txn = get_transaction(txn_id)
    if not txn:
        return jsonify({"success": False, "error": "Not found"}), 404
    product = "disbursement" if txn["type"] == "SEND" else "collection"
    result = check_transaction_status(txn["reference_id"], product)
    if result["success"]:
        status = result.get("status", "").upper()
        if status == "SUCCESSFUL":
            update_status(txn_id, "SUCCESSFUL")
            return jsonify({"success": True, "completed": True, "status": "SUCCESSFUL"})
        elif status == "FAILED":
            update_status(txn_id, "FAILED")
            return jsonify({"success": True, "completed": True, "status": "FAILED"})
    return jsonify({"success": True, "completed": False, "status": "PENDING"})


# ============================================
# API: Balance
# ============================================
@app.route("/api/balance", methods=["GET"])
def api_balance():
    return jsonify(get_balance())


# ============================================
# Helper
# ============================================
def _clean_phone(phone):
    """Normalize any phone format to 250XXXXXXXXX."""
    phone = phone.replace(" ", "").replace("+", "").strip()
    if phone.startswith("0"):
        phone = "25" + phone
    if not phone.startswith("250"):
        phone = "250" + phone
    return phone


# ============================================
# Run
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("  MoMo Tracker - Starting...")
    print(f"  Your number: {MOMO_PHONE_NUMBER}")
    print(f"  Open: http://localhost:5000")
    print("=" * 50)
    app.run(debug=DEBUG, host="0.0.0.0", port=5000)