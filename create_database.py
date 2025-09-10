# pull all the games the player played, and create a database with the pgn information to track the games fast
# with the availability of strong analysis

import requests
import json


username = "TimeDragonGod" # could be automated
game_id = "" # WILL be automated


# User-Agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0'
}

url = f"https://api.chess.com/pub/player/{username}/games/archives"

archives = requests.get(url,headers=headers)

#print(archives.text)
#print(archives.status_code)

for date in json.loads(archives.text)["archives"]:
    print(date)