import os, json
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
DATA_FILE = "/tmp/momo_data.json"
BASE = os.path.dirname(os.path.abspath(__file__))

def ld():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE) as f: return json.load(f)

def sd(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f)

@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.route("/api/sync", methods=["GET"])
def gd():
    return jsonify({"txns": ld()})

@app.route("/api/sync", methods=["POST"])
def pd():
    d = request.get_json(force=True) or {}
    sd(d.get("txns", []))
    return jsonify({"ok": True, "count": len(d.get("txns", []))})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
