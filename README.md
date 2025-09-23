# chess-free-analysis

> A Firefox extension with a Python backend that adds a **Free Review** button to Chess.com, fetches your games via the Chess.com API into a local SQLite database, and with one click opens the selected game on `wintrchess.com/analysis` by automatically sending its PGN.
<img width="1388" height="933" alt="Screenshot_20250922_163406" src="https://github.com/user-attachments/assets/08a7d50e-bf98-4f2d-8484-e226bb01109c" />

## Features
- Injects a **Free Review** button next to Chess.com’s **Review** link.  
- **Auto-starts** and **auto-stops** the local Flask server via a Native Messaging Host (no manual server steps).
- Fetches all your **Chess.com** games to the database. (Does sync with not tracked games)
- Reads PGN from `/<username>.db` (SQLite).
- Sends the PGN to **wintrchess.com/analysis** and triggers **Analyze**.  
- Simple config: **`username.txt`** (first line = your chess.com username).


## Overview
1. On Chess.com’s game-over pop up, click **Free Review**.  
2. The extension asks a **Native Host** to start Flask (if not already running).  
3. Background calls `http://127.0.0.1:5000/run` with the current Review URL.  
4. Flask fetches untracked games,updates the database and looks up the PGN in `<username>.db` and returns it.  
5. The extension opens **wintrchess.com/analysis**, injects the PGN, and clicks **Analyze**.  
6. The extension asks the Native Host to **stop** Flask.

## Usage

### Dependencies
- Python 3.10+
- Firefox
- Python libs:
  ```
  Flask==3.1.2
  requests==2.32.5
  ```
  Install with:
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

### Prerequisites

**1) Username**
```bash
# repo server folder
printf "<YOUR_CHESS_USERNAME>\n" > username.txt
```

**2) Native host (auto-start)**
Make sure `server_starter.py` is executable and has a shebang:
```bash
# line 1 of server_starter.py should be:
# !/usr/bin/env python3
chmod +x server_starter.py
```
Install the host manifest (Firefox • Linux):
```bash
NAME="com.example.server_starter"
EXT_ID="free-chess-analysis@dragon"
TARGET="$HOME/.mozilla/native-messaging-hosts"
HOST="$(realpath ./server_starter.py)"   # handles paths with spaces

mkdir -p "$TARGET"
cat > "$TARGET/$NAME.json" <<JSON
{
  "name": "$NAME",
  "description": "Starts my local Flask server on demand",
  "path": "$HOST",
  "type": "stdio",
  "allowed_extensions": ["$EXT_ID"]
}
JSON
```

**3) Load the extension**
- **Temporary (dev):** open `about:debugging#/runtime/this-firefox` => **Load Temporary Add-on..** => select `manifest.json`.  
- **Permanent:** sign as **unlisted** on AMO and install the signed XPI.


## Legal & Disclaimer

- This project is **unofficial** and is **not affiliated with, endorsed, or sponsored by Chess.com or WintrChess**. All trademarks are the property of their respective owners.  
- Use is intended for **personal, non‑commercial purposes** with data you can already access under your own account.  
- Use at your own risk.
