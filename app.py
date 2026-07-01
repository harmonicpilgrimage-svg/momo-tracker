import os
import json
import logging
import threading
import re
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.environ.get('MOMO_DATA_FILE', os.path.join(BASE, 'momo_data.json'))

logger = logging.getLogger('momotracker')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = Flask(__name__, static_folder='static', static_url_path='/static')
_lock = threading.Lock()

def ld():
    try:
        if not os.path.exists(DATA_FILE):
            return []
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        logger.exception('Failed to load data file')
        return []

def sd(d):
    tmp = DATA_FILE + '.tmp'
    with _lock:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)


# --- SMS parsing and webhook support ---
_sms_api_key = os.environ.get('SMS_API_KEY')

def auto_cat_py(t):
    x = (t.get('description','') + ' ' + t.get('notes','') + ' ' + t.get('raw_message','')).lower()
    patterns = [
        (r'restaurant|food|lunch|dinner|breakfast|grocer|market|cafe|coffee|meal|pizza|burger', 'Food'),
        (r'transport|taxi|moto|bus|fuel|gas|fare|ride|uber', 'Transport'),
        (r'rent|bill|electric|water|internet|wifi|airtime|subscription|insurance', 'Bills'),
        (r'shop|buy|cloth|amazon|mall|store|purchase|order', 'Shopping'),
        (r'movie|netflix|spotify|concert|party|bar|club', 'Entertainment'),
        (r'doctor|hospital|clinic|pharm', 'Health'),
        (r'transfer|sent|receive|momo|mobile money|bank|deposit|withdraw', 'Transfer'),
    ]
    for p, cat in patterns:
        if re.search(p, x):
            return cat
    return 'Other'

def parse_message_py(raw):
    if not raw or not raw.strip():
        return None
    t = raw.strip()
    r = {'type': 'expense', 'amount': None, 'currency': 'RWF', 'sender': None, 'receiver': None, 'date': datetime.utcnow().isoformat() + 'Z', 'source': 'sms', 'description': None, 'raw_message': t}
    # amount extraction
    m = re.search(r'(\d[\d,]*)\s*(RWF|FRW|\$|USD|EUR)', t, re.I)
    if not m:
        m = re.search(r'RWF\s*(\d[\d,]*)', t, re.I)
    if not m:
        m = re.search(r'(\d[\d,]+)', t)
    if m:
        try:
            r['amount'] = int(m.group(1).replace(',', ''))
        except Exception:
            r['amount'] = 0
    else:
        r['amount'] = 0
        r['parse_error'] = 'No amount found'
    if re.search(r'RWF|FRW', t, re.I):
        r['currency'] = 'RWF'
    elif re.search(r'\$|USD', t, re.I):
        r['currency'] = 'USD'
    # type
    if re.search(r'receive|received|incoming|income|deposit|credit', t, re.I):
        r['type'] = 'income'
    elif re.search(r'sent|paid|purchased|bought|transfer to|cash out|withdraw', t, re.I):
        r['type'] = 'expense'
    # phone
    p = re.search(r'(250\d{9}|07[0-9]\d{7})', t)
    if p:
        r['receiver'] = p.group(0)
    # date (simple)
    d = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', t)
    if d:
        try:
            dt = d.group(1)
            # naive parsing, assume dd/mm/yyyy or dd/mm/yy
            parts = re.split('[/-]', dt)
            day = int(parts[0]); month = int(parts[1]); year = int(parts[2])
            if year < 100:
                year += 2000
            r['date'] = datetime(year, month, day).isoformat() + 'Z'
        except Exception:
            pass
    # description
    desc = re.search(r'(?:for|description|reason|purpose)[:\s]+(.+?)(?:\.|,|\n|$)', t, re.I)
    if desc:
        r['description'] = desc.group(1).strip()
    else:
        lines = [ln for ln in re.split('[\n\r]+', t) if ln.strip()]
        if lines:
            r['description'] = lines[0][:80]
    r['category'] = auto_cat_py(r)
    r['id'] = str(uuid.uuid4())
    return r


@app.route('/')
def index():
    return send_from_directory(BASE, 'index.html')

@app.route('/api/sync', methods=['GET'])
def get_sync():
    return jsonify({'txns': ld()})

@app.route('/api/sync', methods=['POST'])
def post_sync():
    if not request.is_json:
        return jsonify({'error': 'expected json'}), 400
    data = request.get_json() or {}
    txns = data.get('txns')
    if not isinstance(txns, list):
        return jsonify({'error': 'txns must be a list'}), 400
    sd(txns)
    logger.info('Saved %d transactions', len(txns))
    return jsonify({'ok': True, 'count': len(txns)})


@app.route('/api/receive-sms', methods=['POST'])
def receive_sms():
    # simple API key auth
    key = request.headers.get('X-API-KEY') or request.headers.get('Authorization')
    if _sms_api_key:
        if not key or (key != _sms_api_key and not key.startswith('Bearer ' + _sms_api_key)):
            return jsonify({'error': 'unauthorized'}), 401
    # accept JSON or form
    data = {}
    if request.is_json:
        data = request.get_json() or {}
    else:
        data['raw'] = request.form.get('raw') or request.form.get('message')
        data['sender'] = request.form.get('sender')
    raw = data.get('raw') or data.get('message') or ''
    if not raw:
        return jsonify({'error': 'no_message'}), 400
    txn = parse_message_py(raw)
    if not txn:
        return jsonify({'error': 'could_not_parse'}), 400
    # attach optional metadata
    if data.get('sender'):
        txn['sender'] = data.get('sender')
    txns = ld()
    txns.insert(0, txn)
    sd(txns)
    logger.info('Received SMS txn id=%s amount=%s', txn.get('id'), txn.get('amount'))
    return jsonify({'ok': True, 'id': txn.get('id')}), 201

@app.errorhandler(500)
def handle_500(e):
    logger.exception('Unhandled exception')
    return jsonify({'error': 'internal_server_error'}), 500

if __name__ == '__main__':
    app.run(host=os.environ.get('FLASK_RUN_HOST', '0.0.0.0'), port=int(os.environ.get('FLASK_RUN_PORT', 8080)))
