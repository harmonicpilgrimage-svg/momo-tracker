import traceback, json
from flask import Flask, request, jsonify
from config import SECRET_KEY, DEBUG, MOMO_PHONE_NUMBER
from momo_api import send_money, request_payment, check_transaction_status, get_balance
from sms_parser import parse_momo_sms, is_momo_sms
from database import (add_transaction, update_note, update_status, get_all_transactions, get_transaction, get_stats)

app = Flask(__name__)
app.secret_key = SECRET_KEY

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>MoMo Tracker</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#f5f7fb;--card:#fff;--accent:#f7931a;--accent2:#ffb347;--text:#1a1d28;--sub:#6b7280;--green:#10b981;--red:#ef4444;--blue:#3b82f6;--purple:#8b5cf6;--radius:18px;--shadow:0 1px 2px rgba(0,0,0,.04),0 4px 16px rgba(0,0,0,.06);--shadow-lg:0 4px 24px rgba(0,0,0,.1)}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',-apple-system,sans-serif;background:var(--bg);color:var(--text);max-width:480px;margin:0 auto;min-height:100vh;overflow-x:hidden}
.nav{padding:20px 20px 12px;display:flex;justify-content:space-between;align-items:center}
.nav .logo{font-size:22px;font-weight:800;letter-spacing:-.5px;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.nav .phone{font-size:11px;color:var(--sub);background:var(--card);padding:6px 12px;border-radius:20px;font-weight:500;box-shadow:var(--shadow)}
.hero{background:linear-gradient(135deg,#1a1d28,#2d1f0f);margin:0 16px;border-radius:var(--radius);padding:24px;color:#fff;position:relative;overflow:hidden;box-shadow:var(--shadow-lg)}
.hero::after{content:'';position:absolute;top:-40px;right:-40px;width:120px;height:120px;background:rgba(247,147,26,.15);border-radius:50%}
.hero .balance-label{font-size:12px;opacity:.7;text-transform:uppercase;letter-spacing:1px}
.hero .balance-amount{font-size:36px;font-weight:800;margin:4px 0;letter-spacing:-1px}
.hero .balance-amt{font-size:36px;font-weight:800;margin:4px 0;letter-spacing:-1px;display:inline}
.hero-row{display:flex;gap:16px;margin-top:16px}
.hero-stat{flex:1}
.hero-stat .val{font-size:15px;font-weight:700}
.hero-stat .lbl{font-size:10px;opacity:.6;text-transform:uppercase;letter-spacing:.5px}
.quick-actions{display:flex;gap:10px;padding:16px}
.quick-btn{flex:1;padding:16px 12px;border:none;border-radius:14px;font-size:13px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;transition:all .15s;box-shadow:var(--shadow)}
.quick-btn:active{transform:scale(.96)}
.quick-btn .icon{font-size:22px}
.quick-btn.paste{background:var(--card);color:var(--text);border:2px dashed #e5e7eb}
.quick-btn.send{background:var(--red);color:#fff}
.quick-btn.request{background:var(--green);color:#fff}
.section{margin:0 16px 8px}
.section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.section-header h3{font-size:14px;font-weight:700}
.section-header .count{font-size:11px;color:var(--sub);background:#e5e7eb;padding:3px 10px;border-radius:10px}
.txn-card{background:var(--card);border-radius:14px;padding:16px;margin-bottom:8px;box-shadow:var(--shadow);cursor:pointer;transition:all .15s;border-left:4px solid transparent;display:flex;gap:12px;align-items:flex-start}
.txn-card:hover{border-left-color:var(--accent)}
.txn-card.sent{border-left-color:var(--red)}
.txn-card.received{border-left-color:var(--green)}
.txn-icon{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.txn-icon.sent{background:#fef2f2;color:var(--red)}
.txn-icon.received{background:#ecfdf5;color:var(--green)}
.txn-body{flex:1;min-width:0}
.txn-body .txn-type{font-size:13px;font-weight:600;margin-bottom:2px}
.txn-body .txn-amount{font-size:17px;font-weight:700}
.txn-body .txn-phone{font-size:11px;color:var(--sub);margin-top:2px}
.txn-body .txn-date{font-size:10px;color:#9ca3af;margin-top:1px}
.txn-note-badge{margin-top:6px;padding:6px 10px;background:#fffbeb;border-radius:8px;font-size:11px;color:#92400e;font-weight:500;display:inline-block}
.txn-note-badge.empty{background:#fef2f2;color:var(--red)}
.txn-status{font-size:9px;padding:3px 8px;border-radius:8px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;flex-shrink:0}
.txn-status.ok{background:#ecfdf5;color:#065f46}
.txn-status.badge{font-size:9px;padding:2px 6px;border-radius:6px;margin-left:6px;font-weight:600}
.badge-sms{background:#e0e7ff;color:#3730a3}
.badge-paste{background:#fef3c7;color:#92400e}
.empty{margin:32px 16px;text-align:center;padding:40px 20px;background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow)}
.empty .icon{font-size:48px;margin-bottom:12px}
.empty h4{font-size:15px;margin-bottom:4px}
.empty p{font-size:12px;color:var(--sub);line-height:1.5}
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:200;justify-content:center;align-items:flex-end}
.modal-overlay.active{display:flex}
.modal{background:var(--card);border-radius:20px 20px 0 0;padding:24px 20px 32px;width:100%;max-width:480px;max-height:85vh;overflow-y:auto;animation:slideUp .2s ease}
@keyframes slideUp{from{transform:translateY(100%)}to{transform:translateY(0)}}
.modal h2{font-size:17px;margin-bottom:6px;font-weight:700}
.modal .modal-hint{font-size:12px;color:var(--sub);margin-bottom:16px;line-height:1.5}
.modal textarea,.modal input{width:100%;padding:14px;border:2px solid #e5e7eb;border-radius:12px;font-size:15px;font-family:inherit;margin-bottom:12px;resize:vertical;transition:border .2s}
.modal textarea:focus,.modal input:focus{outline:none;border-color:var(--accent)}
.modal textarea{height:130px;font-family:'SF Mono','Menlo',monospace;font-size:13px}
.modal-actions{display:flex;gap:10px}
.modal-actions .btn{flex:1;padding:14px;border:none;border-radius:12px;font-size:14px;font-weight:600;cursor:pointer;transition:all .15s}
.modal-actions .btn:active{transform:scale(.97)}
.btn-ghost{background:#f3f4f6;color:var(--text)}
.btn-primary{background:var(--accent);color:#fff}
.btn-danger{background:var(--red);color:#fff}
.export-bar{padding:0 16px 20px;display:flex;gap:8px}
.export-btn{flex:1;padding:12px;border:1.5px solid #e5e7eb;border-radius:12px;background:var(--card);font-size:12px;font-weight:600;cursor:pointer;text-align:center;color:var(--text)}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1a1d28;color:#fff;padding:12px 24px;border-radius:30px;font-size:13px;font-weight:600;z-index:300;opacity:0;transition:opacity .3s;box-shadow:0 8px 30px rgba(0,0,0,.25)}
.toast.show{opacity:1}
</style>
</head>
<body>

<div class="nav"><span class="logo">MoMoTracker</span><span class="phone">{{ my_number }}</span></div>

<div class="hero">
  <div class="balance-label">Monthly Overview</div>
  <div><span class="balance-amount">{{ stats.total_sent }}</span> <span style="font-size:14px;opacity:.6">RWF sent</span></div>
  <div class="hero-row">
    <div class="hero-stat"><div class="val">{{ stats.total_transactions }}</div><div class="lbl">Transactions</div></div>
    <div class="hero-stat"><div class="val">{{ stats.total_received }} RWF</div><div class="lbl">Received</div></div>
    <div class="hero-stat"><div class="val">{{ stats.with_notes }}/{{ stats.total_transactions }}</div><div class="lbl">With Notes</div></div>
  </div>
</div>

<div class="quick-actions">
  <button class="quick-btn paste" onclick="openPaste()"><span class="icon">📋</span>Paste SMS</button>
  <button class="quick-btn send" onclick="openForm('SEND')"><span class="icon">📤</span>Send</button>
  <button class="quick-btn request" onclick="openForm('REQUEST')"><span class="icon">📥</span>Request</button>
</div>

<div class="export-bar">
  <button class="export-btn" onclick="exportCSV()">📊 Export CSV</button>
  <button class="export-btn" onclick="location.reload()">🔄 Refresh</button>
</div>

<div class="section">
  <div class="section-header"><h3>Recent Transactions</h3><span class="count">{{ stats.total_transactions }} total</span></div>
  {{ txn_html }}
</div>

<!-- Paste Modal -->
<div class="modal-overlay" id="paste-modal">
<div class="modal">
<h2>📋 Paste MoMo SMS</h2>
<div class="modal-hint">Copy the SMS you received from MTN MoMo after your transaction and paste it below. The amount, phone number, and type will be detected automatically.</div>
<div id="paste-error" style="color:var(--red);font-size:12px;margin-bottom:10px;display:none"></div>
<textarea id="paste-text" placeholder="Paste your MoMo SMS here...&#10;&#10;For example: You have sent 5000 RWF to Jean 250781234567 on 30/06/2026 at 14:30"></textarea>
<div class="modal-actions"><button class="btn btn-ghost" onclick="closePaste()">Cancel</button><button class="btn btn-primary" onclick="submitPaste()">Save Transaction</button></div>
</div>
</div>

<!-- Send/Request Modal -->
<div class="modal-overlay" id="form-modal">
<div class="modal">
<h2 id="form-title">Send Money</h2>
<div id="form-error" style="color:var(--red);font-size:12px;margin-bottom:10px;display:none"></div>
<input type="tel" id="form-phone" placeholder="Phone (078xxxxxxx)">
<input type="number" id="form-amount" placeholder="Amount in RWF" min="1">
<textarea id="form-note" placeholder="What is this for? (e.g. rent, groceries)" style="height:70px;font-family:inherit;font-size:15px"></textarea>
<div class="modal-actions"><button class="btn btn-ghost" onclick="closeForm()">Cancel</button><button class="btn btn-primary" id="form-submit-btn" onclick="submitForm()">Send</button></div>
</div>
</div>

<!-- Note Modal -->
<div class="modal-overlay" id="note-modal">
<div class="modal">
<h2>📝 Add Note</h2>
<div class="modal-hint">What was this money used for? Keep it short and clear.</div>
<div id="note-error" style="color:var(--red);font-size:12px;margin-bottom:10px;display:none"></div>
<input type="hidden" id="note-txn-id">
<textarea id="note-text" placeholder="e.g. paid rent, bought groceries, transport fare..." style="font-family:inherit;font-size:15px;height:80px"></textarea>
<div class="modal-actions"><button class="btn btn-ghost" onclick="closeNote()">Skip</button><button class="btn btn-primary" onclick="saveNote()">Save Note</button></div>
</div>
</div>

<div class="toast" id="toast"></div>

<script>
function openPaste(){document.getElementById('paste-text').value='';document.getElementById('paste-error').style.display='none';document.getElementById('paste-modal').classList.add('active')}
function closePaste(){document.getElementById('paste-modal').classList.remove('active')}
async function submitPaste(){
  const t=document.getElementById('paste-text').value.trim(),e=document.getElementById('paste-error');
  e.style.display='none';
  if(!t){e.textContent='Paste your MoMo SMS first';e.style.display='block';return}
  try{
    const r=await fetch('/api/paste-sms',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sms:t})});
    const d=await r.json();
    if(d.success){closePaste();tst(d.message);if(d.transaction_id)setTimeout(()=>openNote(d.transaction_id,''),1500);setTimeout(()=>location.reload(),2500)}
    else{e.textContent=d.error;e.style.display='block'}
  }catch(x){e.textContent='Connection error';e.style.display='block'}
}
var cur='SEND';
function openForm(a){cur=a;document.getElementById('form-title').textContent=a==='SEND'?'📤 Send Money':'📥 Request Payment';document.getElementById('form-submit-btn').textContent=a==='SEND'?'Send Money':'Request Payment';document.getElementById('form-error').style.display='none';document.getElementById('form-phone').value='';document.getElementById('form-amount').value='';document.getElementById('form-note').value='';document.getElementById('form-modal').classList.add('active')}
function closeForm(){document.getElementById('form-modal').classList.remove('active')}
async function submitForm(){
  const p=document.getElementById('form-phone').value.trim(),a=document.getElementById('form-amount').value.trim(),n=document.getElementById('form-note').value.trim(),e=document.getElementById('form-error'),b=document.getElementById('form-submit-btn');
  e.style.display='none';
  if(!p){e.textContent='Enter phone number';e.style.display='block';return}
  if(!a||parseInt(a)<=0){e.textContent='Enter valid amount';e.style.display='block';return}
  b.disabled=true;b.textContent='Processing...';
  try{
    const r=await fetch(cur==='SEND'?'/api/send':'/api/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:p,amount:parseInt(a),note:n})});
    const d=await r.json();
    if(d.success){closeForm();tst(d.message);if(!n&&d.transaction_id)setTimeout(()=>openNote(d.transaction_id,''),1500);setTimeout(()=>location.reload(),2500)}
    else{e.textContent=d.error;e.style.display='block'}
  }catch(x){e.textContent='Connection error';e.style.display='block'}
  finally{b.disabled=false;b.textContent=cur==='SEND'?'Send Money':'Request Payment'}
}
function openNote(id,n){document.getElementById('note-txn-id').value=id;document.getElementById('note-text').value=n||'';document.getElementById('note-error').style.display='none';document.getElementById('note-modal').classList.add('active')}
function closeNote(){document.getElementById('note-modal').classList.remove('active')}
async function saveNote(){
  const id=document.getElementById('note-txn-id').value,n=document.getElementById('note-text').value.trim(),e=document.getElementById('note-error');
  if(!n){e.textContent='Write something';e.style.display='block';return}
  try{
    const r=await fetch('/api/transaction/'+id+'/note',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({note:n})});
    const d=await r.json();
    if(d.success){closeNote();tst('Note saved! ✅');location.reload()}
    else{e.textContent=d.error;e.style.display='block'}
  }catch(x){e.textContent='Connection error';e.style.display='block'}
}
function tst(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2800)}
function exportCSV(){
  let csv='Type,Phone,Amount,Status,Note,Date\n';
  document.querySelectorAll('.txn-card').forEach(c=>{
    const type=c.querySelector('.txn-type')?.textContent?.trim()||'';
    const phone=c.querySelector('.txn-phone')?.textContent?.replace('To: ','').replace('From: ','').trim()||'';
    const amount=c.querySelector('.txn-amount')?.textContent?.replace(' RWF','').trim()||'';
    const status=c.querySelector('.txn-status')?.textContent?.trim()||'';
    const note=c.querySelector('.txn-note-badge')?.textContent?.replace('📝 ','').trim()||'';
    const date=c.querySelector('.txn-date')?.textContent?.trim()||'';
    csv+=[type,phone,amount,status,note,date].map(v=>'"'+v.replace(/"/g,'""')+'"').join(',')+'\n';
  });
  const b=new Blob([csv],{type:'text/csv'});
  const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='momo-transactions.csv';a.click()
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    try:
        txns = get_all_transactions()
        stats = get_stats()
        if txns:
            parts = []
            for txn in txns:
                t = txn["type"]
                if t == "SEND": card_cls, icon_cls, icon, label = "sent", "sent", "↑", "Sent to"
                elif t == "RECEIVE": card_cls, icon_cls, icon, label = "received", "received", "↓", "Received from"
                else: card_cls, icon_cls, icon, label = "received", "received", "↓", "Requested from"

                ref = txn.get("reference_id","")
                if ref.startswith("sms-"): badge = '<span class="badge-sms txn-status badge">📱 SMS</span>'
                elif ref.startswith("paste-"): badge = '<span class="badge-paste txn-status badge">📋 Paste</span>'
                else: badge = ""

                note_html = ""
                if txn.get("note"):
                    note_html = f'<div class="txn-note-badge">📝 {txn["note"]}</div>'
                else:
                    note_html = '<div class="txn-note-badge empty">⚠️ Tap to add note</div>'

                created = txn.get("created_at","")
                d = created[:10] if len(created)>10 else ""
                tm = created[11:16] if len(created)>16 else ""
                note_esc = (txn.get("note") or "").replace("\\","\\\\").replace("'","\\'")

                parts.append(f"""<div class="txn-card {card_cls}" onclick="openNote('{txn['id']}','{note_esc}')">
<div class="txn-icon {icon_cls}">{icon}</div>
<div class="txn-body">
<div class="txn-type">{label} {badge}</div>
<div class="txn-amount">{txn['amount']} RWF</div>
<div class="txn-phone">{txn['phone_number']}</div>
<div class="txn-date">{d} at {tm}</div>
{note_html}
</div>
<span class="txn-status ok">{txn['status']}</span>
</div>""")
            txn_html = "".join(parts)
        else:
            txn_html = """<div class="empty"><div class="icon">📭</div><h4>No transactions yet</h4><p>Do a MoMo transaction, copy the SMS receipt,<br>and tap <b>Paste SMS</b> above to track it.</p></div>"""

        html = PAGE_HTML
        for k, v in {
            "{{ my_number }}": MOMO_PHONE_NUMBER,
            "{{ stats.total_transactions }}": str(stats["total_transactions"]),
            "{{ stats.with_notes }}": str(stats["with_notes"]),
            "{{ stats.total_sent }}": str(stats["total_sent"]),
            "{{ stats.total_received }}": str(stats["total_received"]),
            "{{ txn_html }}": txn_html,
        }.items():
            html = html.replace(k, v)
        return html
    except Exception:
        return f"<h1>App Error</h1><pre>{traceback.format_exc()}</pre>", 500


@app.route("/api/paste-sms", methods=["POST"])
def api_paste_sms():
    data = request.get_json(silent=True) or {}
    sms_text = data.get("sms", data.get("text", request.get_data(as_text=True)))
    if not sms_text: return jsonify({"success": False, "error": "No text provided."}), 400
    parsed = parse_momo_sms(sms_text)
    if not parsed["amount"]: return jsonify({"success": False, "error": "Could not find an amount. Make sure it says something like '5000 RWF'."}), 400
    phone = parsed["phone"] or "N/A"
    txn_type = parsed["type"] if parsed["type"] != "UNKNOWN" else "SEND"
    txn = add_transaction(txn_type, phone, parsed["amount"], f"paste-{parsed.get('date','')}-{parsed.get('time','')}", "SUCCESSFUL")
    return jsonify({"success": True, "transaction_id": txn["id"], "parsed": parsed, "message": f"✅ {txn_type} of {parsed['amount']} RWF saved!"})


@app.route("/api/sms", methods=["POST"])
def api_sms():
    # Grab the text from any possible format
    sms_text = ""
    try:
        data = request.get_json(silent=True) or {}
        sms_text = data.get("sms") or data.get("text") or data.get("body") or data.get("message") or ""
    except:
        pass
    if not sms_text:
        sms_text = request.get_data(as_text=True)
    if not sms_text:
        sms_text = request.form.get("text") or request.form.get("sms") or ""

    # Always return 200 immediately so the phone doesn't time out
    if not sms_text:
        return jsonify({"ok": True})

    # Quick parse and save
    try:
        parsed = parse_momo_sms(sms_text)
        if parsed["amount"]:
            txn_type = parsed["type"] if parsed["type"] != "UNKNOWN" else "SEND"
            add_transaction(txn_type, parsed["phone"] or "N/A", parsed["amount"],
                          f"sms-{parsed.get('date','')}-{parsed.get('time','')}", "SUCCESSFUL")
    except:
        pass  # Never fail — always return ok

    return jsonify({"ok": True})


@app.route("/api/transaction/<txn_id>/note", methods=["POST"])
def api_add_note(txn_id):
    data = request.get_json(silent=True) or {}
    note = data.get("note", "").strip()
    if not note: return jsonify({"success": False, "error": "Note cannot be empty"}), 400
    txn = update_note(txn_id, note)
    return jsonify({"success": True, "transaction": txn}) if txn else (jsonify({"success": False, "error": "Not found"}), 404)


@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.get_json(); phone = _clean_phone(data.get("phone","")); amount = data.get("amount")
    if not phone or len(phone)!=12: return jsonify({"success":False,"error":"Phone must be 12 digits"}),400
    if not amount or not str(amount).isdigit() or int(amount)<=0: return jsonify({"success":False,"error":"Valid amount required"}),400
    amount=int(amount); result=send_money(phone,amount,data.get("note","").strip())
    if not result["success"]: return jsonify(result),500
    txn=add_transaction("SEND",phone,amount,result["reference_id"])
    if data.get("note","").strip(): update_note(txn["id"],data["note"].strip())
    return jsonify({"success":True,"message":result["message"],"transaction_id":txn["id"]})

@app.route("/api/request", methods=["POST"])
def api_request():
    data = request.get_json(); phone = _clean_phone(data.get("phone","")); amount = data.get("amount")
    if not phone or len(phone)!=12: return jsonify({"success":False,"error":"Phone must be 12 digits"}),400
    if not amount or not str(amount).isdigit() or int(amount)<=0: return jsonify({"success":False,"error":"Valid amount required"}),400
    amount=int(amount); result=request_payment(phone,amount,data.get("note","").strip())
    if not result["success"]: return jsonify(result),500
    txn=add_transaction("REQUEST",phone,amount,result["reference_id"])
    if data.get("note","").strip(): update_note(txn["id"],data["note"].strip())
    return jsonify({"success":True,"message":result["message"],"transaction_id":txn["id"]})

@app.route("/api/balance")
def api_balance(): return jsonify(get_balance())

def _clean_phone(p):
    p=p.replace(" ","").replace("+","").strip()
    if p.startswith("0"): p="25"+p
    if not p.startswith("250"): p="250"+p
    return p

if __name__=="__main__": app.run(debug=DEBUG,host="0.0.0.0",port=5000)
