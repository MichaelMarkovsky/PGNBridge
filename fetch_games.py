# pull all the games the player played, and create a database with the pgn information to track the games fast
# with the availability of strong analysis

import requests
import json
import sqlite3
from pathlib import Path

from datetime import date
from urllib.parse import urlparse

username = "TimeDragonGod" # could be automated


# User-Agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0'
}

#=================================Get Archives=======================
def get_archives():
    url = f"https://api.chess.com/pub/player/{username}/games/archives"

    archives = requests.get(url,headers=headers)

    #print(archives.text)
    #print(archives.status_code)

    print(f"{username}'s archives:")
    for date in json.loads(archives.text)["archives"]:
        archives_list.append(date)
        print(date)



#==================================Get Games=======================
def get_games():
    for month in archives_list:
        resp = requests.get(month, headers=headers) # the games of the month that have been played
        for game in json.loads(resp.text)["games"]:
            url = game.get("url")
            pgn = game.get("pgn")
            if url and pgn:  # only add if both exist (pgn might not exist if the game was aborted)
                games.append((url, pgn)) # add each game to the list


    #print(games)
    print(len(games))


#==================================Create Data-base=======================
def create_database():
    conn = sqlite3.connect(f'{username}.db')  # Creates a new database file if it doesn’t exist
    cursor = conn.cursor()

    create_table = """
        CREATE TABLE IF NOT EXISTS games (
            link TEXT PRIMARY KEY,
            pgn TEXT
        );
    """

    cursor.execute(create_table)

    #Insert the games data into the database:
    insert_game = """
        INSERT OR IGNORE INTO games (link, pgn)
        VALUES (?, ?);
    """

    cursor.executemany(insert_game, games)  # games = list of (link, pgn)
    conn.commit()  # one commit at the end

    cursor.close()
    conn.close()

#==================================Sync the data=======================
#a table for a date that was last synced, and fetch the new information 
#via api calls to the games table if the link does not exist
def _archive_month_date(archive_url: str) -> date:
    parts = urlparse(archive_url).path.rstrip("/").split("/")
    y = int(parts[-2]); m = int(parts[-1])
    return date(y, m, 1)

def sync():
    global conn, cursor  # so helpers can use them
    # build archive list (ascending) if not already:
    if not archives_list:
        get_archives()
    if not archives_list:
        print("No archives available.")
        return

    conn = sqlite3.connect(f'{username}.db') 
    cursor = conn.cursor()

    # ensure target tables exist (needed before INSERTs below)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            link TEXT PRIMARY KEY,
            pgn  TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS last_sync (
            sync_date TEXT
        );
    """)

    # check if table is empty
    cursor.execute("SELECT COUNT(*) FROM last_sync;")
    row_count = cursor.fetchone()[0]

    if row_count == 0:
        print("Table is empty, first sync")
        print("Inserting last date from the archive..")
        archive_date_database()
    else:
        print("Table has data, syncing")
        print("Inserting today's date..")
        last_synced = get_last_sync()
        today_month = date(date.today().year, date.today().month, 1)

        to_process = []
        for aurl in archives_list:
            adt = _archive_month_date(aurl)
            if (last_synced is None or adt > last_synced) and adt <= today_month:
                to_process.append(aurl)

        # always refresh the current month if present
        if archives_list and _archive_month_date(archives_list[-1]) == today_month:
            newest = archives_list[-1]
            if newest not in to_process:
                to_process.append(newest)

        total_rows = 0
        for aurl in sorted(to_process, key=_archive_month_date):
            resp = requests.get(aurl, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            batch = []
            for g in data.get("games", []):
                url = g.get("url"); pgn = g.get("pgn")
                if url and pgn:
                    batch.append((url, pgn))

            if batch:
                cursor.executemany(
                    "INSERT OR IGNORE INTO games (link, pgn) VALUES (?, ?);",
                    batch
                )
                total_rows += len(batch)

        conn.commit()
        current_date_database()

    cursor.close()
    conn.close()




def archive_date_database():
    global conn, cursor
    url = archives_list[-1]
    parts = urlparse(url).path.rstrip("/").split("/")
    year = int(parts[-2]); month = int(parts[-1])
    dt = date(year, month, 1)
    cursor.execute("DELETE FROM last_sync;")
    cursor.execute("INSERT INTO last_sync (sync_date) VALUES (?);", (dt.isoformat(),))
    conn.commit()

def current_date_database():
    global conn, cursor
    today = date.today()
    dt = date(today.year, today.month, 1)
    cursor.execute("DELETE FROM last_sync;")
    cursor.execute("INSERT INTO last_sync (sync_date) VALUES (?);", (dt.isoformat(),))
    conn.commit()

def get_last_sync():
    global cursor
    cursor.execute("SELECT sync_date FROM last_sync LIMIT 1;")
    row = cursor.fetchone()
    return None if row is None else date.fromisoformat(row[0])



#===================================================================

archives_list = []
games = [] # a list of tuples of (game url , pgn)



file_path = Path(f"{username}.db")

if file_path.is_file():
    print(f"'{file_path}' exists.")
    print("syncing..")
    sync()
else:
    print(f"'{file_path}' is missing.")
    print("Getting archives..")
    get_archives()
    print("Getting games..")
    get_games()
    print("Creating the database..")
    create_database()
    print("syncing..")
    sync()
