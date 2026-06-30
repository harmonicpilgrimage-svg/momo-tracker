# ============================================
# MoMo Tracker - Main Application
# ============================================
import traceback
from flask import Flask, request, jsonify
from config import SECRET_KEY, DEBUG, MOMO_PHONE_NUMBER
from momo_api import send_money, request_payment, check_transaction_status, get_balance
from sms_parser import parse_momo_sms, is_momo_sms
from database import (
    add_transaction, update_note, update_status,
    get_all_transactions, get_transaction, get_stats,
)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ============================================
# HTML TEMPLATE (embedded)
# ============================================
PAGE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoMo Tracker</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f0f2f5;
            color: #1a1a2e;
            max-width: 600px;
            margin: 0 auto;
            min-height: 100vh;
        }
        .header {
            background: #ffc107;
            color: #1a1a2e;
            padding: 20px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 10;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 22px; }
        .header .subtitle { font-size: 13px; opacity: 0.8; margin-top: 4px; }
        .actions {
            display: flex;
            gap: 10px;
            padding: 15px;
            background: white;
            margin: 10px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .btn {
            flex: 1;
            padding: 14px 10px;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s;
        }
        .btn:active { transform: scale(0.96); }
        .btn-send { background: #e74c3c; color: white; }
        .btn-request { background: #2ecc71; color: white; }
        .btn-balance { background: #3498db; color: white; margin-top: 10px; width: 100%; }
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            padding: 0 10px;
            margin-bottom: 10px;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stat-card .stat-value { font-size: 24px; font-weight: 700; color: #1a1a2e; }
        .stat-card .stat-label { font-size: 12px; color: #666; margin-top: 4px; }
        .section-title { padding: 15px 15px 5px; font-size: 16px; font-weight: 700; color: #333; }
        .txn-list { padding: 0 10px 30px; }
        .txn-card {
            background: white;
            padding: 15px;
            border-radius: 12px;
            margin-bottom: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            cursor: pointer;
        }
        .txn-top { display: flex; justify-content: space-between; align-items: center; }
        .txn-type { font-weight: 700; font-size: 14px; }
        .txn-type.send { color: #e74c3c; }
        .txn-type.receive { color: #2ecc71; }
        .txn-type.request { color: #2ecc71; }
        .txn-amount { font-weight: 700; font-size: 18px; margin-top: 4px; }
        .txn-detail { font-size: 13px; color: #666; margin-top: 2px; }
        .txn-note {
            margin-top: 8px;
            padding: 8px 10px;
            background: #fff8e1;
            border-radius: 8px;
            font-size: 13px;
            color: #555;
            font-style: italic;
        }
        .txn-note.empty { background: #ffeaea; color: #c0392b; font-style: normal; font-weight: 600; }
        .txn-status {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 10px;
            font-weight: 600;
        }
        .status-SUCCESSFUL { background: #d4edda; color: #155724; }
        .status-FAILED { background: #f8d7da; color: #721c24; }
        .status-PENDING { background: #fff3cd; color: #856404; }
        .txn-date { font-size: 11px; color: #999; margin-top: 4px; }
        .badge-sms {
            display: inline-block;
            background: #e8f5e9;
            color: #2e7d32;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 6px;
            margin-left: 6px;
            font-weight: 600;
        }
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.6);
            z-index: 100;
            justify-content: center;
            align-items: center;
        }
        .modal-overlay.active { display: flex; }
        .modal {
            background: white;
            border-radius: 16px;
            padding: 24px;
            width: 90%;
            max-width: 400px;
        }
        .modal h2 { margin-bottom: 15px; font-size: 18px; }
        .modal input, .modal textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            margin-bottom: 12px;
            font-family: inherit;
        }
        .modal input:focus, .modal textarea:focus { outline: none; border-color: #ffc107; }
        .modal textarea { height: 80px; resize: vertical; }
        .modal-actions { display: flex; gap: 10px; }
        .btn-cancel { background: #ddd; color: #333; }
        .btn-submit { background: #ffc107; color: #1a1a2e; }
        .empty-state { text-align: center; padding: 50px 20px; color: #999; }
        .empty-state .icon { font-size: 50px; margin-bottom: 10px; }
        .toast {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #1a1a2e;
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 14px;
            z-index: 200;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .toast.show { opacity: 1; }
    </style>
</head>
<body>
    <div class="header">
        <h1>💰 MTN MoMo Tracker</h1>
        <div class="subtitle">SMS Auto-Detect Active | {{ my_number }}</div>
    </div>
    <div style="padding: 10px;"><button class="btn btn-balance" onclick="checkBalance()">🔍 Check My Balance</button></div>
    <div class="actions">
        <button class="btn btn-send" onclick="openForm('SEND')">📤 Send Money</button>
        <button class="btn btn-request" onclick="openForm('REQUEST')">📥 Request Money</button>
    </div>
    <div class="stats">
        <div class="stat-card"><div class="stat-value">{{ stats.total_transactions }}</div><div class="stat-label">Total Transactions</div></div>
        <div class="stat-card"><div class="stat-value">{{ stats.with_notes }}/{{ stats.total_transactions }}</div><div class="stat-label">With Notes</div></div>
        <div class="stat-card"><div class="stat-value">{{ stats.total_sent }} RWF</div><div class="stat-label">Total Sent</div></div>
        <div class="stat-card"><div class="stat-value">{{ stats.total_received }} RWF</div><div class="stat-label">Total Received</div></div>
    </div>
    <div class="section-title">📋 Your Transactions</div>
    <div class="txn-list" id="txn-list">
        {{ txn_html }}
    </div>

    <!-- Send/Request Modal -->
    <div class="modal-overlay" id="form-modal">
        <div class="modal">
            <h2 id="form-title">Send Money</h2>
            <div id="form-error" style="color:#e74c3c;font-size:13px;margin-bottom:10px;display:none;"></div>
            <input type="tel" id="form-phone" placeholder="Phone number (e.g. 078XXXXXXX)">
            <input type="number" id="form-amount" placeholder="Amount" min="1">
            <textarea id="form-note" placeholder="What is this for? (e.g. rent, groceries)"></textarea>
            <div class="modal-actions">
                <button class="btn btn-cancel" onclick="closeForm()">Cancel</button>
                <button class="btn btn-submit" id="form-submit-btn" onclick="submitForm()">Send</button>
            </div>
        </div>
    </div>

    <!-- Note Modal -->
    <div class="modal-overlay" id="note-modal">
        <div class="modal">
            <h2>📝 Add Note</h2>
            <p style="color:#666;font-size:14px;margin-bottom:12px;">What was this money used for?</p>
            <div id="note-error" style="color:#e74c3c;font-size:13px;margin-bottom:10px;display:none;"></div>
            <input type="hidden" id="note-txn-id">
            <textarea id="note-text" placeholder="e.g. paid rent, bought groceries, transport fare..."></textarea>
            <div class="modal-actions">
                <button class="btn btn-cancel" onclick="closeNoteModal()">Skip</button>
                <button class="btn btn-submit" onclick="saveNote()">Save Note</button>
            </div>
        </div>
    </div>

    <div class="toast" id="toast"></div>

    <script>
        let currentAction = 'SEND';
        function openForm(action) {
            currentAction = action;
            document.getElementById('form-title').textContent = action === 'SEND' ? '📤 Send Money' : '📥 Request Payment';
            document.getElementById('form-submit-btn').textContent = action === 'SEND' ? 'Send Money' : 'Request Payment';
            document.getElementById('form-error').style.display = 'none';
            document.getElementById('form-phone').value = '';
            document.getElementById('form-amount').value = '';
            document.getElementById('form-note').value = '';
            document.getElementById('form-modal').classList.add('active');
        }
        function closeForm() { document.getElementById('form-modal').classList.remove('active'); }
        async function submitForm() {
            const phone = document.getElementById('form-phone').value.trim();
            const amount = document.getElementById('form-amount').value.trim();
            const note = document.getElementById('form-note').value.trim();
            const errorEl = document.getElementById('form-error');
            const btn = document.getElementById('form-submit-btn');
            errorEl.style.display = 'none';
            if (!phone) { errorEl.textContent = 'Please enter a phone number.'; errorEl.style.display = 'block'; return; }
            if (!amount || parseInt(amount) <= 0) { errorEl.textContent = 'Enter a valid amount.'; errorEl.style.display = 'block'; return; }
            btn.disabled = true;
            btn.textContent = 'Processing...';
            const url = currentAction === 'SEND' ? '/api/send' : '/api/request';
            try {
                const resp = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone, amount: parseInt(amount), note }),
                });
                const data = await resp.json();
                if (data.success) {
                    closeForm();
                    showToast(data.message || 'Transaction submitted!');
                    if (!note && data.transaction_id) setTimeout(() => openNoteModal(data.transaction_id, ''), 2000);
                    setTimeout(() => location.reload(), 3000);
                } else {
                    errorEl.textContent = data.error || 'Something went wrong.';
                    errorEl.style.display = 'block';
                }
            } catch (e) {
                errorEl.textContent = 'Connection error.';
                errorEl.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.textContent = currentAction === 'SEND' ? 'Send Money' : 'Request Payment';
            }
        }
        function openNoteModal(txnId, currentNote) {
            document.getElementById('note-txn-id').value = txnId;
            document.getElementById('note-text').value = currentNote || '';
            document.getElementById('note-error').style.display = 'none';
            document.getElementById('note-modal').classList.add('active');
        }
        function closeNoteModal() { document.getElementById('note-modal').classList.remove('active'); }
        async function saveNote() {
            const txnId = document.getElementById('note-txn-id').value;
            const note = document.getElementById('note-text').value.trim();
            const errorEl = document.getElementById('note-error');
            if (!note) { errorEl.textContent = 'Please write something.'; errorEl.style.display = 'block'; return; }
            try {
                const resp = await fetch('/api/transaction/' + txnId + '/note', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ note }),
                });
                const data = await resp.json();
                if (data.success) { closeNoteModal(); showToast('Note saved!'); location.reload(); }
                else { errorEl.textContent = data.error; errorEl.style.display = 'block'; }
            } catch (e) { errorEl.textContent = 'Connection error.'; errorEl.style.display = 'block'; }
        }
        async function checkBalance() {
            showToast('Checking balance...');
            try {
                const resp = await fetch('/api/balance');
                const data = await resp.json();
                showToast(data.success ? 'Balance: ' + (data.balance || 'N/A') : 'Could not get balance');
            } catch (e) { showToast('Connection error.'); }
        }
        function showToast(msg) {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }
    </script>
</body>
</html>"""


# ============================================
# PAGES
# ============================================
@app.route("/")
def index():
    try:
        transactions = get_all_transactions()
        stats = get_stats()

        if transactions:
            txn_parts = []
            for txn in transactions:
                if txn["type"] == "SEND":
                    txn_type_display = "📤 SENT"
                    txn_type_class = "send"
                elif txn["type"] == "RECEIVE":
                    txn_type_display = "📥 RECEIVED"
                    txn_type_class = "receive"
                else:
                    txn_type_display = "📥 REQUESTED"
                    txn_type_class = "request"

                # SMS badge
                sms_badge = ""
                if txn.get("reference_id", "").startswith("sms-"):
                    sms_badge = '<span class="badge-sms">📱 SMS</span>'

                note_html = ""
                if txn.get("note"):
                    note_html = f'<div class="txn-note">📝 {txn["note"]}</div>'
                else:
                    note_html = '<div class="txn-note empty">⚠️ No note — tap to add one!</div>'

                created = txn.get("created_at", "")
                date_str = created[:10] if len(created) > 10 else "N/A"
                time_str = created[11:16] if len(created) > 16 else ""

                note_escaped = txn.get("note") or ""
                note_escaped = note_escaped.replace("\\", "\\\\").replace("'", "\\'")

                txn_parts.append(f"""<div class="txn-card" onclick="openNoteModal('{txn['id']}', '{note_escaped}')">
                <div class="txn-top">
                    <span class="txn-type {txn_type_class}">{txn_type_display} {sms_badge}</span>
                    <span class="txn-status status-{txn['status']}">{txn['status']}</span>
                </div>
                <div class="txn-amount">{txn['amount']} RWF</div>
                <div class="txn-detail">To/From: {txn['phone_number']}</div>
                {note_html}
                <div class="txn-date">{date_str} at {time_str}</div>
            </div>""")
            txn_html = "".join(txn_parts)
        else:
            txn_html = '<div class="empty-state"><div class="icon">📭</div><p>No transactions yet!</p><p style="font-size:13px;">Transactions detected from your SMS will appear here automatically.</p></div>'

        html = PAGE_HTML.replace("{{ my_number }}", MOMO_PHONE_NUMBER)
        html = html.replace("{{ stats.total_transactions }}", str(stats["total_transactions"]))
        html = html.replace("{{ stats.with_notes }}", str(stats["with_notes"]))
        html = html.replace("{{ stats.total_sent }}", str(stats["total_sent"]))
        html = html.replace("{{ stats.total_received }}", str(stats["total_received"]))
        html = html.replace("{{ txn_html }}", txn_html)

        return html
    except Exception as e:
        error_msg = traceback.format_exc()
        return f"<h1>App Error</h1><pre>{error_msg}</pre>", 500


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

    return jsonify({"success": True, "message": result["message"], "transaction_id": txn["id"]})


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

    return jsonify({"success": True, "message": result["message"], "transaction_id": txn["id"]})


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
    phone = phone.replace(" ", "").replace("+", "").strip()
    if phone.startswith("0"):
        phone = "25" + phone
    if not phone.startswith("250"):
        phone = "250" + phone
    return phone


# ============================================
# SMS Webhook - Receives MoMo SMS from MacroDroid
# ============================================
@app.route("/api/sms", methods=["POST"])
def api_sms():
    """Receives SMS text forwarded from MacroDroid on your Android phone."""
    data = request.get_json() if request.is_json else {}
    sms_text = data.get("sms", data.get("text", ""))
    if not sms_text:
        sms_text = request.get_data(as_text=True)

    if not sms_text:
        return jsonify({"success": False, "error": "No SMS text provided"}), 400

    if not is_momo_sms(sms_text):
        return jsonify({"success": False, "error": "Not a MoMo SMS", "detected": False})

    parsed = parse_momo_sms(sms_text)

    if not parsed["amount"]:
        return jsonify({"success": False, "error": "Could not parse amount", "parsed": parsed})

    phone = parsed["phone"] or "N/A"
    txn_type = parsed["type"]
    if txn_type == "UNKNOWN":
        txn_type = "SEND"

    txn = add_transaction(
        txn_type=txn_type,
        phone_number=phone,
        amount=parsed["amount"],
        reference_id=f"sms-{parsed.get('date','')}-{parsed.get('time','')}",
        status="SUCCESSFUL",
    )

    return jsonify({
        "success": True,
        "detected": True,
        "transaction_id": txn["id"],
        "parsed": parsed,
        "message": f"Detected {txn_type} of {parsed['amount']} RWF. Add a note!",
    })


if __name__ == "__main__":
    app.run(debug=DEBUG, host="0.0.0.0", port=5000)