import sqlite3
from fetch_games import username #importing the username and executing "fetch_games.py"

DB_PATH = f"{username}.db"
LINK = "https://www.chess.com/game/live/143185362042"

def get_pgn_by_link(db_path: str, link: str) -> str | None:
    # read-only query; no commit needed
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row  # access columns by name
        cur = conn.execute("SELECT pgn FROM games WHERE link = ?;", (link,))
        row = cur.fetchone()
        return row["pgn"] if row else None

pgn = get_pgn_by_link(DB_PATH, LINK)
if pgn is None:
    print("PGN not found for that link")
else:
    print(pgn)
