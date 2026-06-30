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

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>MoMo Tracker</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f2f5;color:#1a1a2e;max-width:600px;margin:0 auto;min-height:100vh}
.header{background:#ffc107;color:#1a1a2e;padding:16px 20px;text-align:center;position:sticky;top:0;z-index:10;box-shadow:0 2px 8px rgba(0,0,0,.1)}
.header h1{font-size:20px}
.header .subtitle{font-size:12px;opacity:.8;margin-top:3px}
.paste-btn{width:calc(100% - 20px);margin:12px 10px;padding:18px;background:#1a1a2e;color:#ffc107;border:none;border-radius:14px;font-size:17px;font-weight:700;cursor:pointer}
.paste-btn:active{transform:scale(.97)}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:0 10px;margin:0 0 10px}
.stat-card{background:#fff;padding:14px;border-radius:12px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.1)}
.stat-card .stat-value{font-size:22px;font-weight:700;color:#1a1a2e}
.stat-card .stat-label{font-size:11px;color:#666;margin-top:3px}
.section-title{padding:15px 15px 5px;font-size:15px;font-weight:700;color:#333}
.txn-list{padding:0 10px 30px}
.txn-card{background:#fff;padding:14px;border-radius:12px;margin-bottom:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);cursor:pointer}
.txn-top{display:flex;justify-content:space-between;align-items:center}
.txn-type{font-weight:700;font-size:13px}
.txn-type.send{color:#e74c3c}
.txn-type.receive{color:#2ecc71}
.txn-type.request{color:#2ecc71}
.txn-amount{font-weight:700;font-size:17px;margin-top:3px}
.txn-detail{font-size:12px;color:#666;margin-top:2px}
.txn-note{margin-top:7px;padding:7px 10px;background:#fff8e1;border-radius:8px;font-size:12px;color:#555;font-style:italic}
.txn-note.empty{background:#ffeaea;color:#c0392b;font-style:normal;font-weight:600}
.txn-status{font-size:10px;padding:2px 7px;border-radius:10px;font-weight:600}
.status-SUCCESSFUL{background:#d4edda;color:#155724}
.status-FAILED{background:#f8d7da;color:#721c24}
.status-PENDING{background:#fff3cd;color:#856404}
.txn-date{font-size:10px;color:#999;margin-top:3px}
.badge-sms{display:inline-block;background:#e8f5e9;color:#2e7d32;font-size:9px;padding:2px 5px;border-radius:5px;margin-left:5px;font-weight:600}
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);z-index:100;justify-content:center;align-items:center}
.modal-overlay.active{display:flex}
.modal{background:#fff;border-radius:16px;padding:22px;width:92%;max-width:400px;max-height:90vh;overflow-y:auto}
.modal h2{margin-bottom:12px;font-size:17px}
.modal textarea{width:100%;padding:12px;border:2px solid #ddd;border-radius:10px;font-size:15px;margin-bottom:12px;font-family:monospace;height:150px;resize:vertical}
.modal textarea:focus{outline:none;border-color:#ffc107}
.modal input{width:100%;padding:12px;border:2px solid #ddd;border-radius:10px;font-size:15px;margin-bottom:12px;font-family:inherit}
.modal input:focus{outline:none;border-color:#ffc107}
.modal-actions{display:flex;gap:10px}
.btn{flex:1;padding:13px 10px;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer}
.btn-cancel{background:#ddd;color:#333}
.btn-submit{background:#ffc107;color:#1a1a2e}
.empty-state{text-align:center;padding:40px 20px;color:#999}
.empty-state .icon{font-size:45px;margin-bottom:8px}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#1a1a2e;color:#fff;padding:12px 22px;border-radius:25px;font-size:13px;z-index:200;opacity:0;transition:opacity .3s}
.toast.show{opacity:1}
.hint{font-size:11px;color:#999;margin-top:6px;text-align:center;line-height:1.5}
</style>
</head>
<body>
<div class="header"><h1>💰 MTN MoMo Tracker</h1><div class="subtitle">{{ my_number }}</div></div>

<button class="paste-btn" onclick="openPasteModal()">📋 Paste SMS Here</button>
<p class="hint">After any MoMo transaction,<br>copy the SMS text and paste it here.<br>It will be saved automatically with a note prompt.</p>

<div class="stats">
  <div class="stat-card"><div class="stat-value">{{ stats.total_transactions }}</div><div class="stat-label">Total</div></div>
  <div class="stat-card"><div class="stat-value">{{ stats.with_notes }}/{{ stats.total_transactions }}</div><div class="stat-label">With Notes</div></div>
  <div class="stat-card"><div class="stat-value">{{ stats.total_sent }} RWF</div><div class="stat-label">Sent</div></div>
  <div class="stat-card"><div class="stat-value">{{ stats.total_received }} RWF</div><div class="stat-label">Received</div></div>
</div>

<div class="section-title">📋 Transactions</div>
<div class="txn-list">{{ txn_html }}</div>

<!-- Paste SMS Modal -->
<div class="modal-overlay" id="paste-modal">
<div class="modal">
<h2>📋 Paste MoMo SMS</h2>
<p style="font-size:12px;color:#666;margin-bottom:10px">1. Open your SMS app<br>2. Copy the MoMo transaction message<br>3. Paste it below</p>
<div id="paste-error" style="color:#e74c3c;font-size:12px;margin-bottom:8px;display:none"></div>
<textarea id="paste-text" placeholder="Paste your MoMo SMS here...&#10;&#10;Example: You have sent 5000 RWF to Jean 250781234567 on 30/06/2026 at 14:30"></textarea>
<div class="modal-actions">
<button class="btn btn-cancel" onclick="closePasteModal()">Cancel</button>
<button class="btn btn-submit" onclick="submitPaste()">Save Transaction</button>
</div>
</div>
</div>

<!-- Note Modal -->
<div class="modal-overlay" id="note-modal">
<div class="modal">
<h2>📝 Add Note</h2>
<p style="color:#666;font-size:13px;margin-bottom:10px">What was this money used for?</p>
<div id="note-error" style="color:#e74c3c;font-size:12px;margin-bottom:8px;display:none"></div>
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
function openPasteModal(){
  document.getElementById('paste-text').value='';
  document.getElementById('paste-error').style.display='none';
  document.getElementById('paste-modal').classList.add('active');
}
function closePasteModal(){document.getElementById('paste-modal').classList.remove('active')}

async function submitPaste(){
  const text=document.getElementById('paste-text').value.trim();
  const err=document.getElementById('paste-error');
  err.style.display='none';
  if(!text){err.textContent='Please paste your MoMo SMS first.';err.style.display='block';return}
  try{
    const resp=await fetch('/api/paste-sms',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sms:text})});
    const data=await resp.json();
    if(data.success){
      closePasteModal();
      showToast(data.message||'Transaction saved!');
      if(data.transaction_id)setTimeout(()=>openNoteModal(data.transaction_id,''),1500);
      setTimeout(()=>location.reload(),3000);
    }else{
      err.textContent=data.error||'Could not parse this SMS. Make sure it is a MoMo message.';
      err.style.display='block';
    }
  }catch(e){err.textContent='Connection error. Try again.';err.style.display='block'}
}

function openNoteModal(id,note){
  document.getElementById('note-txn-id').value=id;
  document.getElementById('note-text').value=note||'';
  document.getElementById('note-error').style.display='none';
  document.getElementById('note-modal').classList.add('active');
}
function closeNoteModal(){document.getElementById('note-modal').classList.remove('active')}
async function saveNote(){
  const id=document.getElementById('note-txn-id').value;
  const note=document.getElementById('note-text').value.trim();
  const err=document.getElementById('note-error');
  if(!note){err.textContent='Please write something.';err.style.display='block';return}
  try{
    const resp=await fetch('/api/transaction/'+id+'/note',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({note})});
    const data=await resp.json();
    if(data.success){closeNoteModal();showToast('Note saved! ✅');location.reload()}
    else{err.textContent=data.error;err.style.display='block'}
  }catch(e){err.textContent='Connection error.';err.style.display='block'}
}
function showToast(m){
  const t=document.getElementById('toast');
  t.textContent=m;t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),3000);
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    try:
        transactions = get_all_transactions()
        stats = get_stats()
        if transactions:
            txn_parts = []
            for txn in transactions:
                if txn["type"] == "SEND":
                    disp, cls = "📤 SENT", "send"
                elif txn["type"] == "RECEIVE":
                    disp, cls = "📥 RECEIVED", "receive"
                else:
                    disp, cls = "📥 REQUESTED", "request"
                sms_badge = '<span class="badge-sms">📱 SMS</span>' if txn.get("reference_id","").startswith("sms-") else ""
                paste_badge = '<span class="badge-sms" style="background:#fff3e0;color:#e65100">📋 PASTE</span>' if txn.get("reference_id","").startswith("paste-") else ""
                badge = sms_badge or paste_badge
                note_html = f'<div class="txn-note">📝 {txn["note"]}</div>' if txn.get("note") else '<div class="txn-note empty">⚠️ No note — tap to add!</div>'
                created = txn.get("created_at","")
                d = created[:10] if len(created)>10 else "N/A"
                t = created[11:16] if len(created)>16 else ""
                note_esc = (txn.get("note") or "").replace("\\","\\\\").replace("'","\\'")
                txn_parts.append(f"""<div class="txn-card" onclick="openNoteModal('{txn['id']}','{note_esc}')">
<div class="txn-top"><span class="txn-type {cls}">{disp} {badge}</span><span class="txn-status status-{txn['status']}">{txn['status']}</span></div>
<div class="txn-amount">{txn['amount']} RWF</div>
<div class="txn-detail">To/From: {txn['phone_number']}</div>
{note_html}
<div class="txn-date">{d} at {t}</div></div>""")
            txn_html = "".join(txn_parts)
        else:
            txn_html = '<div class="empty-state"><div class="icon">📭</div><p>No transactions yet!</p><p style="font-size:12px">Do a MoMo transaction, copy the SMS,<br>and tap "Paste SMS Here" above.</p></div>'
        html = PAGE_HTML.replace("{{ my_number }}", MOMO_PHONE_NUMBER)
        html = html.replace("{{ stats.total_transactions }}", str(stats["total_transactions"]))
        html = html.replace("{{ stats.with_notes }}", str(stats["with_notes"]))
        html = html.replace("{{ stats.total_sent }}", str(stats["total_sent"]))
        html = html.replace("{{ stats.total_received }}", str(stats["total_received"]))
        html = html.replace("{{ txn_html }}", txn_html)
        return html
    except Exception as e:
        return f"<h1>App Error</h1><pre>{traceback.format_exc()}</pre>", 500


# ============================================
# API: Paste SMS (THE MAIN WAY TO TRACK TRANSACTIONS)
# ============================================
@app.route("/api/paste-sms", methods=["POST"])
def api_paste_sms():
    """User pastes MoMo SMS text. We parse it and save the transaction."""
    data = request.get_json(silent=True) or {}
    sms_text = data.get("sms", data.get("text", ""))
    if not sms_text:
        sms_text = request.get_data(as_text=True)

    if not sms_text:
        return jsonify({"success": False, "error": "No text provided. Please paste your MoMo SMS."}), 400

    parsed = parse_momo_sms(sms_text)

    if not parsed["amount"]:
        return jsonify({
            "success": False,
            "error": "Could not find an amount in this message. Are you sure it's a MoMo SMS? It should contain something like '5000 RWF'."
        }), 400

    phone = parsed["phone"] or "N/A"
    txn_type = parsed["type"]
    if txn_type == "UNKNOWN":
        txn_type = "SEND"

    txn = add_transaction(
        txn_type=txn_type,
        phone_number=phone,
        amount=parsed["amount"],
        reference_id=f"paste-{parsed.get('date','')}-{parsed.get('time','')}",
        status="SUCCESSFUL",
    )

    return jsonify({
        "success": True,
        "transaction_id": txn["id"],
        "parsed": parsed,
        "message": f"✅ {txn_type} of {parsed['amount']} RWF saved! Add a note below."
    })


# ============================================
# API: SMS Webhook (for future auto-detection)
# ============================================
@app.route("/api/sms", methods=["POST"])
def api_sms():
    data = request.get_json(silent=True) or {}
    sms_text = data.get("sms", data.get("text", ""))
    if not sms_text:
        sms_text = request.get_data(as_text=True)
    if not sms_text:
        return jsonify({"success": False, "error": "No SMS text"}), 400
    if not is_momo_sms(sms_text):
        return jsonify({"success": False, "error": "Not a MoMo SMS", "detected": False})
    parsed = parse_momo_sms(sms_text)
    if not parsed["amount"]:
        return jsonify({"success": False, "error": "Could not parse", "parsed": parsed})
    phone = parsed["phone"] or "N/A"
    txn_type = parsed["type"]
    if txn_type == "UNKNOWN":
        txn_type = "SEND"
    txn = add_transaction(txn_type=txn_type, phone_number=phone, amount=parsed["amount"], reference_id=f"sms-{parsed.get('date','')}-{parsed.get('time','')}", status="SUCCESSFUL")
    return jsonify({"success": True, "detected": True, "transaction_id": txn["id"], "parsed": parsed, "message": f"Detected {txn_type} of {parsed['amount']} RWF. Add a note!"})


# ============================================
# API: Add Note
# ============================================
@app.route("/api/transaction/<txn_id>/note", methods=["POST"])
def api_add_note(txn_id):
    data = request.get_json(silent=True) or {}
    note = data.get("note", "").strip()
    if not note:
        return jsonify({"success": False, "error": "Note cannot be empty"}), 400
    txn = update_note(txn_id, note)
    if txn:
        return jsonify({"success": True, "transaction": txn})
    return jsonify({"success": False, "error": "Transaction not found"}), 404


# ============================================
# Legacy API endpoints
# ============================================
@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.get_json()
    phone = _clean_phone(data.get("phone", ""))
    amount = data.get("amount")
    note = data.get("note", "").strip()
    if not phone or len(phone) != 12:
        return jsonify({"success": False, "error": "Phone must be 12 digits"}), 400
    if not amount or not str(amount).isdigit() or int(amount) <= 0:
        return jsonify({"success": False, "error": "Enter a valid amount"}), 400
    amount = int(amount)
    result = send_money(phone, amount, payer_message=note)
    if not result["success"]:
        return jsonify(result), 500
    txn = add_transaction("SEND", phone, amount, result["reference_id"])
    if note: update_note(txn["id"], note)
    return jsonify({"success": True, "message": result["message"], "transaction_id": txn["id"]})

@app.route("/api/request", methods=["POST"])
def api_request():
    data = request.get_json()
    phone = _clean_phone(data.get("phone", ""))
    amount = data.get("amount")
    note = data.get("note", "").strip()
    if not phone or len(phone) != 12:
        return jsonify({"success": False, "error": "Phone must be 12 digits"}), 400
    if not amount or not str(amount).isdigit() or int(amount) <= 0:
        return jsonify({"success": False, "error": "Enter a valid amount"}), 400
    amount = int(amount)
    result = request_payment(phone, amount, note=note)
    if not result["success"]:
        return jsonify(result), 500
    txn = add_transaction("REQUEST", phone, amount, result["reference_id"])
    if note: update_note(txn["id"], note)
    return jsonify({"success": True, "message": result["message"], "transaction_id": txn["id"]})

@app.route("/api/transaction/<txn_id>/check", methods=["POST"])
def api_check_status(txn_id):
    txn = get_transaction(txn_id)
    if not txn: return jsonify({"success": False, "error": "Not found"}), 404
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

@app.route("/api/balance", methods=["GET"])
def api_balance():
    return jsonify(get_balance())

def _clean_phone(phone):
    phone = phone.replace(" ", "").replace("+", "").strip()
    if phone.startswith("0"): phone = "25" + phone
    if not phone.startswith("250"): phone = "250" + phone
    return phone

if __name__ == "__main__":
    app.run(debug=DEBUG, host="0.0.0.0", port=5000)
