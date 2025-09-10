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

#=================================Get Archives=======================

url = f"https://api.chess.com/pub/player/{username}/games/archives"

archives = requests.get(url,headers=headers)

#print(archives.text)
#print(archives.status_code)

archives_list = []

print(f"{username}'s archives:")
for date in json.loads(archives.text)["archives"]:
    archives_list.append(date)
    print(date)



#==================================Get Games=======================

games = [] # a list of tuples of (game url , pgn)

for month in archives_list:
    resp = requests.get(month, headers=headers) # the games of the month that have been played
    for game in json.loads(resp.text)["games"]:
        url = game.get("url")
        pgn = game.get("pgn")
        if url and pgn:  # only add if both exist (pgn might not exist if the game was aborted)
            games.append((url, pgn)) # add each game to the list


print(games)
print(len(games))


#==================================Create Data-base=======================
# create the database if it does not exist