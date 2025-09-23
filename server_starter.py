#!/usr/bin/env python3
import sys, json, struct, subprocess, socket, os, signal, time
from pathlib import Path

# Project layout:
#   chess-free-analysis/
#     server_starter.py   <-- this file
#     server/
#       app.py            <-- Flask entry
#       venv/             <-- (venv with Flask)

REPO_ROOT = Path(__file__).resolve().parent
APP_DIR   = REPO_ROOT / "server"
APP_ENTRY = APP_DIR / "app.py"
PORT      = 5000
PIDFILE   = Path.home() / ".local/share/server_starter_flask.pid"
LOGFILE   = Path.home() / ".local/state/server_starter.log"
LOGFILE.parent.mkdir(parents=True, exist_ok=True)

def log(msg: str):
    with LOGFILE.open("a", encoding="utf-8") as f:
        f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + msg + "\n")

def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), 0.25):
            return True
    except Exception:
        return False

def read_msg():
    raw_len = sys.stdin.buffer.read(4)
    if not raw_len:
        return None
    n = struct.unpack("<I", raw_len)[0]
    data = sys.stdin.buffer.read(n)
    return json.loads(data)

def write_msg(obj):
    b = json.dumps(obj).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(b)))
    sys.stdout.buffer.write(b)
    sys.stdout.buffer.flush()

def pick_python() -> str:
    # Look for venv, .venv, .env inside server/
    candidates = [
        APP_DIR / "venv"  / "bin" / "python",
        APP_DIR / ".venv" / "bin" / "python",
        APP_DIR / ".env"  / "bin" / "python",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return sys.executable

def kill_stale_pidfile():
    """Remove a stale pidfile without touching processes."""
    try:
        if PIDFILE.exists():
            PIDFILE.unlink()
    except Exception:
        pass

def stop_flask():
    """Stop Flask using the recorded PID, with TERM then KILL fallback."""
    if not PIDFILE.exists():
        # No pidfile; try to detect server by port and kill it (best-effort)
        if port_open(PORT):
            log("No pidfile, but port is open; attempting best-effort kill by port is skipped for safety.")
        return {"ok": False, "message": "No pidfile / Flask not running"}

    try:
        pid = int(PIDFILE.read_text().strip())
    except Exception as e:
        kill_stale_pidfile()
        return {"ok": False, "message": f"Invalid pidfile: {e}"}

    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.4)
        # If still running, escalate
        try:
            os.kill(pid, 0)  # still alive?
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.2)
        except Exception:
            pass
    except ProcessLookupError:
        pass
    except Exception as e:
        log(f"Stop error: {e}")
        kill_stale_pidfile()
        return {"ok": False, "message": f"Failed to stop: {e}"}

    kill_stale_pidfile()
    # Wait briefly for port to close
    for _ in range(30):
        if not port_open(PORT):
            break
        time.sleep(0.1)

    log(f"Stopped Flask (pid {pid})")
    return {"ok": True, "message": f"Stopped Flask (pid {pid})"}

def start_flask():
    if port_open(PORT):
        return {"ok": True, "message": f"Flask already running on {PORT}"}

    if not APP_ENTRY.exists():
        msg = f"app.py not found at {APP_ENTRY}"
        log(msg)
        return {"ok": False, "message": msg}

    # If there is a PIDFILE but the process is gone, clean it
    if PIDFILE.exists():
        try:
            pid = int(PIDFILE.read_text().strip())
            os.kill(pid, 0)  # raises if not alive
        except Exception:
            kill_stale_pidfile()

    PYTHON = pick_python()

    try:
        log(f"Starting Flask with: {PYTHON} {APP_ENTRY} (cwd={APP_DIR})")
        logf = LOGFILE.open("a")
        proc = subprocess.Popen(
            [PYTHON, str(APP_ENTRY)],
            cwd=str(APP_DIR),
            stdout=logf, stderr=logf,
            start_new_session=True, close_fds=True
        )
        PIDFILE.write_text(str(proc.pid))
    except Exception as e:
        msg = f"Failed to launch: {e}"
        log(msg)
        return {"ok": False, "message": msg}

    for _ in range(100):  # wait up to 10s
        if port_open(PORT):
            log("Flask reported up on port 5000")
            return {"ok": True, "message": f"Flask started on {PORT}"}
        time.sleep(0.1)

    log("Timeout waiting for Flask to bind")
    return {"ok": False, "message": "Timeout starting Flask"}

def status_flask():
    running = port_open(PORT)
    pid_txt = PIDFILE.read_text().strip() if PIDFILE.exists() else None
    return {"ok": True, "running": running, "pid": pid_txt}

def main():
    msg = read_msg()
    if not msg:
        return
    action = msg.get("action")
    if action == "start":
        write_msg(start_flask())
    elif action == "stop":
        write_msg(stop_flask())
    elif action == "status":
        write_msg(status_flask())
    elif action == "restart":
        stop_flask()
        write_msg(start_flask())
    else:
        write_msg({"ok": False, "message": f"unknown action {action}"})

if __name__ == "__main__":
    main()
