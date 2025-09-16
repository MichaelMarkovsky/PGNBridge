from flask import Flask, request, jsonify
from subprocess import run, CalledProcessError
import os

API_KEY = os.getenv("EXT_API_KEY", "dev-secret")  

app = Flask(__name__)

@app.after_request
def add_cors(resp):
    # allow extension/content-script to call this server
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Api-Key"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return resp

@app.route("/run", methods=["POST", "OPTIONS"])
def run_script():
    if request.method == "OPTIONS":
        return ("", 204)
    if request.headers.get("X-Api-Key") != API_KEY:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    arg = data.get("arg", "")

    try:
        res = run(
            ["python", "fetch_games.py", arg],
            capture_output=True,
            text=True,
            check=True
        )
        return jsonify({"ok": True, "stdout": res.stdout, "stderr": res.stderr})
    except CalledProcessError as e:
        return jsonify({"ok": False, "stdout": e.stdout, "stderr": e.stderr}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
