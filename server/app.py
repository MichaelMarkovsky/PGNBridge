from flask import Flask, request, jsonify
import sqlite3, os
from pathlib import Path  
from subprocess import run, CalledProcessError
import sqlite3, os, sys

API_KEY = os.getenv("EXT_API_KEY", "dev-secret")
USERNAME = "TimeDragonGod"
DB_PATH  = f"{USERNAME}.db"

app = Flask(__name__)

@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Api-Key"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return resp

def get_pgn_by_link(link: str) -> str | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT pgn FROM games WHERE link = ?;", (link,)).fetchone()
        return row["pgn"] if row else None

@app.route("/run", methods=["POST", "OPTIONS"])
def run_script():
    if request.method == "OPTIONS":
        return ("", 204)
    if request.headers.get("X-Api-Key") != API_KEY:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    link = (request.get_json(silent=True) or {}).get("link", "")
    if not link:
        return jsonify({"ok": False, "error": "missing link"}), 400

    # execute fetch_games.py
    script_dir = Path(__file__).resolve().parent
    sync_script = script_dir / "fetch_games.py"
    try:
        res = run([sys.executable, str(sync_script)],
                  cwd=str(script_dir), capture_output=True, text=True, check=True)
    except CalledProcessError as e:
        return jsonify({"ok": False, "error": "sync_failed", "stdout": e.stdout, "stderr": e.stderr}), 500

    pgn = get_pgn_by_link(link)
    return jsonify({"ok": True, "found": bool(pgn), "pgn": pgn or ""})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
