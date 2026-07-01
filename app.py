from flask import Flask, render_template, send_from_directory, request, jsonify
import json, os

app = Flask(__name__)
DATA_FILE = "/tmp/momo_data.json"

def load_server_data():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE) as f: return json.load(f)

def save_server_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

@app.route("/api/sync", methods=["GET"])
def get_data():
    return jsonify({"txns": load_server_data()})

@app.route("/api/sync", methods=["POST"])
def save_data():
    data = request.get_json(force=True) or {}
    txns = data.get("txns", [])
    save_server_data(txns)
    return jsonify({"ok": True, "count": len(txns)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)