from flask import Flask, request, jsonify
import os, sys, sqlite3
from pathlib import Path
from subprocess import run, CalledProcessError

API_KEY  = os.getenv("EXT_API_KEY", "dev-secret")
BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)

@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Api-Key"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return resp

# read username from username.txt
def read_username() -> str:
    p = BASE_DIR / "username.txt"
    try:
        first = (p.read_text(encoding="utf-8").splitlines() or [""])[0].strip()
    except FileNotFoundError:
        raise RuntimeError("username.txt missing")
    if not first:
        raise RuntimeError("username.txt is empty")
    return first

def get_pgn_by_link(db_path: Path, link: str) -> str | None:
    # avoid creating a new empty DB if it doesnt exist
    if not db_path.exists():
        return None
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT pgn FROM games WHERE link = ?;", (link,)).fetchone()
        return row["pgn"] if row else None

@app.route("/run", methods=["POST", "OPTIONS"])
def run_script():
    if request.method == "OPTIONS":
        return ("", 204)
    if request.headers.get("X-Api-Key") != API_KEY:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    link = (request.get_json(silent=True) or {}).get("link", "").strip()
    if not link:
        return jsonify({"ok": False, "error": "missing link"}), 400

    # read username from file
    try:
        username = read_username()
    except RuntimeError as e:
        return jsonify({"ok": False, "error": "username-not-configured", "detail": str(e)}), 400

    db_path = BASE_DIR / f"{username}.db"

    # execute fetch_games.py 
    sync_script = BASE_DIR / "fetch_games.py"
    try:
        res = run([sys.executable, str(sync_script)],
                  cwd=str(BASE_DIR), capture_output=True, text=True, check=True)
    except CalledProcessError as e:
        return jsonify({"ok": False, "error": "sync_failed", "stdout": e.stdout, "stderr": e.stderr}), 500

    pgn = get_pgn_by_link(db_path, link)
    return jsonify({"ok": True, "found": bool(pgn), "pgn": pgn or ""})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
