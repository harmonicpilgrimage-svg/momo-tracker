import os
import json
import logging
import threading
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

@app.errorhandler(500)
def handle_500(e):
    logger.exception('Unhandled exception')
    return jsonify({'error': 'internal_server_error'}), 500

if __name__ == '__main__':
    app.run(host=os.environ.get('FLASK_RUN_HOST', '0.0.0.0'), port=int(os.environ.get('FLASK_RUN_PORT', 8080)))
