import traceback, json
from flask import Flask, request, jsonify, send_from_directory, redirect
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
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#f7931a">
<title>MoMo Tracker</title>
<style>
:root{--bg:#f5f7fb;--card:#fff;--accent:#f7931a;--accent2:#ffb347;--text:#1a1d28;--sub:#6b7280;--green:#10b981;--red:#ef4444;--radius:18px;--shadow:0 1px 2px rgba(0,0,0,.04),0 4px 16px rgba(0,0,0,.06)}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);max-width:480px;margin:0 auto;min-height:100vh}
.nav{padding:16px 20px 10px;display:flex;justify-content:space-between;align-items:center}
.nav .logo{font-size:20px;font-weight:800;color:var(--accent)}
.nav .phone{font-size:11px;color:var(--sub);background:var(--card);padding:6px 12px;border-radius:20px;box-shadow:var(--shadow)}
.hero{background:linear-gradient(135deg,#1a1d28,#2d1f0f);margin:0 16px;border-radius:var(--radius);padding:22px;color:#fff;position:relative;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.12)}
.hero::after{content:'';position:absolute;top:-40px;right:-40px;width:120px;height:120px;background:rgba(247,147,26,.15);border-radius:50%}
.hero .lbl{font-size:11px;opacity:.7;text-transform:uppercase;letter-spacing:1px}
.hero .val{font-size:34px;font-weight:800;margin:2px 0;letter-spacing:-1px}
.hero-row{display:flex;gap:14px;margin-top:14px}
.hero-stat{flex:1}.hero-stat .v{font-size:14px;font-weight:700}.hero-stat .l{font-size:10px;opacity:.6;text-transform:uppercase}
.quick-actions{display:flex;gap:10px;padding:14px 16px}
.quick-btn{flex:1;padding:14px 10px;border:none;border-radius:14px;font-size:13px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:6px;box-shadow:var(--shadow);transition:transform .12s}
.quick-btn:active{transform:scale(.96)}
.quick-btn .ic{font-size:20px}
.quick-btn.paste{background:var(--card);color:var(--text);border:2px dashed #e5e7eb}
.quick-btn.share{background:#1a1d28;color:#ffc107}
.quick-btn.send{background:var(--red);color:#fff}
.section{margin:0 16px 8px}
.section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.section-header h3{font-size:14px;font-weight:700}
.section-header .count{font-size:11px;color:var(--sub);background:#e5e7eb;padding:3px 10px;border-radius:10px}
.txn-card{background:var(--card);border-radius:14px;padding:14px;margin-bottom:8px;box-shadow:var(--shadow);cursor:pointer;border-left:4px solid transparent;display:flex;gap:10px;align-items:flex-start}
.txn-card.sent{border-left-color:var(--red)}
.txn-card.received{border-left-color:var(--green)}
.txn-icon{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0}
.txn-icon.sent{background:#fef2f2;color:var(--red)}
.txn-icon.received{background:#ecfdf5;color:var(--green)}
.txn-body{flex:1;min-width:0}
.txn-body .txn-type{font-size:12px;font-weight:600;margin-bottom:1px}
.txn-body .txn-amount{font-size:16px;font-weight:700}
.txn-body .txn-phone{font-size:11px;color:var(--sub);margin-top:2px}
.txn-body .txn-date{font-size:10px;color:#9ca3af;margin-top:1px}
.txn-note-badge{margin-top:6px;padding:5px 8px;background:#fffbeb;border-radius:6px;font-size:11px;color:#92400e;font-weight:500;display:inline-block}
.txn-note-badge.empty{background:#fef2f2;color:var(--red)}
.txn-status{font-size:9px;padding:2px 7px;border-radius:6px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;flex-shrink:0}
.txn-status.ok{background:#ecfdf5;color:#065f46}
.badge-sms{background:#e0e7ff;color:#3730a3;margin-left:4px}
.badge-paste{background:#fef3c7;color:#92400e;margin-left:4px}
.empty{margin:32px 16px;text-align:center;padding:40px 20px;background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow)}
.empty .icon{font-size:48px;margin-bottom:12px}
.empty h4{font-size:15px;margin-bottom:4px}
.empty p{font-size:12px;color:var(--sub);line-height:1.5}
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:200;justify-content:center;align-items:flex-end}
.modal-overlay.active{display:flex}
.modal{background:var(--card);border-radius:20px 20px 0 0;padding:22px 20px 30px;width:100%;max-width:480px;max-height:85vh;overflow-y:auto;animation:up .2s}
@keyframes up{from{transform:translateY(100%)}to{transform:translateY(0)}}
.modal h2{font-size:17px;margin-bottom:4px;font-weight:700}
.modal .hint{font-size:12px;color:var(--sub);margin-bottom:14px;line-height:1.4}
.modal textarea,.modal input{width:100%;padding:12px;border:2px solid #e5e7eb;border-radius:10px;font-size:15px;font-family:inherit;margin-bottom:10px;resize:vertical}
.modal textarea:focus,.modal input:focus{outline:none;border-color:var(--accent)}
.modal textarea{height:120px;font-size:13px;font-family:monospace}
.modal-actions{display:flex;gap:10px}
.modal-actions .btn{flex:1;padding:13px;border:none;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer}
.modal-actions .btn:active{transform:scale(.97)}
.btn-ghost{background:#f3f4f6;color:var(--text)}
.btn-primary{background:var(--accent);color:#fff}
.btn-danger{background:var(--red);color:#fff}
.export-bar{padding:0 16px 16px;display:flex;gap:8px}
.export-btn{flex:1;padding:10px;border:1.5px solid #e5e7eb;border-radius:10px;background:var(--card);font-size:12px;font-weight:600;cursor:pointer;text-align:center;color:var(--text)}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1a1d28;color:#fff;padding:12px 22px;border-radius:30px;font-size:13px;font-weight:600;z-index:300;opacity:0;transition:opacity .3s;box-shadow:0 8px 30px rgba(0,0,0,.25)}
.toast.show{opacity:1}
</style>
</head>
<body>

<div class="nav"><span class="logo">MoMoTracker</span><span class="phone">{{ my_number }}</span></div>

<div class="hero">
  <div class="lbl">Overview</div>
  <div><span class="val">{{ stats.total_sent }}</span> <span style="font-size:13px;opacity:.6">RWF sent</span></div>
  <div class="hero-row">
    <div class="hero-stat"><div class="v">{{ stats.total_transactions }}</div><div class="l">Total</div></div>
    <div class="hero-stat"><div class="v">{{ stats.total_received }} RWF</div><div class="l">Received</div></div>
    <div class="hero-stat"><div class="v">{{ stats.with_notes }}/{{ stats.total_transactions }}</div><div class="l">Notes</div></div>
  </div>
</div>

<div class="quick-actions">
  <button class="quick-btn share" onclick="openShareModal()"><span class="ic">📱</span>Share SMS</button>
  <button class="quick-btn paste" onclick="openPaste()"><span class="ic">📋</span>Paste</button>
</div>

<div class="export-bar">
  <button class="export-btn" onclick="exportCSV()">📊 Export CSV</button>
  <button class="export-btn" onclick="location.reload()">🔄 Refresh</button>
</div>

<div class="section">
  <div class="section-header"><h3>Recent</h3><span class="count">{{ stats.total_transactions }} txns</span></div>
  {{ txn_html }}
</div>

<!-- Share SMS Modal (explains how to use Android Share) -->
<div class="modal-overlay" id="share-modal">
<div class="modal">
<h2>📱 Share SMS</h2>
<div class="hint">
  <b>1.</b> Open your SMS app<br>
  <b>2.</b> Long-press the MoMo SMS message<br>
  <b>3.</b> Tap <b>Share</b> → Choose <b>MoMo Tracker</b><br><br>
  If MoMo Tracker doesn't appear in the share menu,<br>add this site to your home screen first.
</div>
<div class="modal-actions"><button class="btn btn-ghost" onclick="closeShareModal()">Got it</button></div>
</div>
</div>

<!-- Paste Modal -->
<div class="modal-overlay" id="paste-modal">
<div class="modal">
<h2>📋 Paste MoMo SMS</h2>
<div class="hint">Copy your MoMo SMS and paste it here.</div>
<div id="paste-error" style="color:var(--red);font-size:12px;margin-bottom:8px;display:none"></div>
<textarea id="paste-text" placeholder="Paste your MoMo SMS here..."></textarea>
<div class="modal-actions"><button class="btn btn-ghost" onclick="closePaste()">Cancel</button><button class="btn btn-primary" onclick="submitPaste()">Save</button></div>
</div>
</div>

<!-- Note Modal -->
<div class="modal-overlay" id="note-modal">
<div class="modal">
<h2>📝 Add Note</h2>
<div class="hint">What was this money used for?</div>
<div id="note-error" style="color:var(--red);font-size:12px;margin-bottom:8px;display:none"></div>
<input type="hidden" id="note-txn-id">
<textarea id="note-text" placeholder="e.g. paid rent, bought groceries..." style="font-family:inherit;font-size:15px;height:80px"></textarea>
<div class="modal-actions"><button class="btn btn-ghost" onclick="closeNote()">Skip</button><button class="btn btn-primary" onclick="saveNote()">Save</button></div>
</div>
</div>

<div class="toast" id="toast"></div>

<script>
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js')}

function openShareModal(){document.getElementById('share-modal').classList.add('active')}
function closeShareModal(){document.getElementById('share-modal').classList.remove('active')}

function openPaste(){document.getElementById('paste-text').value='';document.getElementById('paste-error').style.display='none';document.getElementById('paste-modal').classList.add('active')}
function closePaste(){document.getElementById('paste-modal').classList.remove('active')}
async function submitPaste(){
  var t=document.getElementById('paste-text').value.trim(),e=document.getElementById('paste-error');
  e.style.display='none';
  if(!t){e.textContent='Paste your MoMo SMS first';e.style.display='block';return}
  try{
    var r=await fetch('/api/paste-sms',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sms:t})});
    var d=await r.json();
    if(d.success){closePaste();tst(d.message);if(d.transaction_id)setTimeout(function(){openNote(d.transaction_id,'')},1200);setTimeout(function(){location.reload()},2000)}
    else{e.textContent=d.error;e.style.display='block'}
  }catch(x){e.textContent='Connection error';e.style.display='block'}
}

function openNote(id,n){document.getElementById('note-txn-id').value=id;document.getElementById('note-text').value=n||'';document.getElementById('note-error').style.display='none';document.getElementById('note-modal').classList.add('active')}
function closeNote(){document.getElementById('note-modal').classList.remove('active')}
async function saveNote(){
  var id=document.getElementById('note-txn-id').value,n=document.getElementById('note-text').value.trim(),e=document.getElementById('note-error');
  if(!n){e.textContent='Write something';e.style.display='block';return}
  try{
    var r=await fetch('/api/transaction/'+id+'/note',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({note:n})});
    var d=await r.json();
    if(d.success){closeNote();tst('Note saved!');location.reload()}
    else{e.textContent=d.error;e.style.display='block'}
  }catch(x){e.textContent='Connection error';e.style.display='block'}
}

function tst(m){var t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(function(){t.classList.remove('show')},2500)}

function exportCSV(){
  var csv='Type,Phone,Amount,Status,Note,Date\n';
  document.querySelectorAll('.txn-card').forEach(function(c){
    var type=c.querySelector('.txn-type')?c.querySelector('.txn-type').textContent.trim().replace(/[📱📋]/g,'').trim():'';
    var phone=c.querySelector('.txn-phone')?c.querySelector('.txn-phone').textContent.trim():'';
    var amount=c.querySelector('.txn-amount')?c.querySelector('.txn-amount').textContent.replace(' RWF','').trim():'';
    var status=c.querySelector('.txn-status')?c.querySelector('.txn-status').textContent.trim():'';
    var note=c.querySelector('.txn-note-badge')?c.querySelector('.txn-note-badge').textContent.replace('📝 ','').trim():'';
    if(note==='⚠️ Tap to add note')note='';
    var date=c.querySelector('.txn-date')?c.querySelector('.txn-date').textContent.trim():'';
    csv+=[type,phone,amount,status,note,date].map(function(v){return'"'+v.replace(/"/g,'""')+'"'}).join(',')+'\n';
  });
  var b=new Blob([csv],{type:'text/csv'});
  var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='momo-transactions.csv';a.click()
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
                else: card_cls, icon_cls, icon, label = "received", "received", "↓", "Requested"

                ref = txn.get("reference_id","")
                if ref.startswith("sms-"): badge = '<span class="badge-sms txn-status badge">📱</span>'
                elif ref.startswith("paste-"): badge = '<span class="badge-paste txn-status badge">📋</span>'
                elif ref.startswith("share-"): badge = '<span class="badge-sms txn-status badge">📱</span>'
                else: badge = ""

                note_html = f'<div class="txn-note-badge">📝 {txn["note"]}</div>' if txn.get("note") else '<div class="txn-note-badge empty">⚠️ Tap to add note</div>'
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
            txn_html = """<div class="empty"><div class="icon">📭</div><h4>No transactions yet</h4><p>Do a MoMo transaction, then long-press the SMS<br>→ Share → choose MoMo Tracker to auto-track it.</p></div>"""

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


# ============================================
# PWA / Share Target endpoints
# ============================================
@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")

@app.route("/sw.js")
def sw():
    return send_from_directory("static", "sw.js")

@app.route("/icon.png")
def icon():
    return send_from_directory("static", "icon.png")

@app.route("/share", methods=["POST"])
def share():
    """Web Share Target - receives SMS shared from Android SMS app"""
    text = request.form.get("text", "")
    if not text:
        text = request.form.get("title", "")

    if text:
        parsed = parse_momo_sms(text)
        if parsed["amount"]:
            txn_type = parsed["type"] if parsed["type"] != "UNKNOWN" else "SEND"
            txn = add_transaction(txn_type, parsed["phone"] or "N/A", parsed["amount"],
                                  f"share-{parsed.get('date','')}-{parsed.get('time','')}", "SUCCESSFUL")

    return redirect("/")


# ============================================
# API endpoints
# ============================================
@app.route("/api/paste-sms", methods=["POST"])
def api_paste_sms():
    data = request.get_json(silent=True) or {}
    sms_text = data.get("sms") or data.get("text") or request.get_data(as_text=True)
    if not sms_text: return jsonify({"success": False, "error": "No text provided"}), 400
    parsed = parse_momo_sms(sms_text)
    if not parsed["amount"]: return jsonify({"success": False, "error": "Could not find amount. Does it contain 'XXXX RWF'?"}), 400
    txn_type = parsed["type"] if parsed["type"] != "UNKNOWN" else "SEND"
    txn = add_transaction(txn_type, parsed["phone"] or "N/A", parsed["amount"],
                          f"paste-{parsed.get('date','')}-{parsed.get('time','')}", "SUCCESSFUL")
    return jsonify({"success": True, "transaction_id": txn["id"], "message": f"Saved {txn_type} of {parsed['amount']} RWF!"})

@app.route("/api/sms", methods=["POST"])
def api_sms():
    text = ""
    try:
        data = request.get_json(silent=True) or {}
        text = data.get("sms") or data.get("text") or data.get("body") or data.get("message") or ""
    except: pass
    if not text: text = request.get_data(as_text=True)
    if not text: text = request.form.get("text") or request.form.get("sms") or ""
    if not text: return jsonify({"ok": True})

    try:
        parsed = parse_momo_sms(text)
        if parsed["amount"]:
            txn_type = parsed["type"] if parsed["type"] != "UNKNOWN" else "SEND"
            add_transaction(txn_type, parsed["phone"] or "N/A", parsed["amount"],
                          f"sms-{parsed.get('date','')}-{parsed.get('time','')}", "SUCCESSFUL")
    except: pass
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
