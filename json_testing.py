import requests
import json

def get_player_position(playerId):
    player_curl=(f"http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{playerId}?lang=en&region=us")
    player_raw=get_json_response(player_curl)
    position=player_raw["position"]
    player_position=position["abbreviation"]
    return player_position

def QB_Tackles_In_Game(gameId):
    game_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="+str(gameId)
    game_message=""
    game_raw=get_json_response(game_url)
    boxscore=game_raw["boxscore"]
    tackles=0
    if "players" in boxscore:
        player_game_stats=boxscore["players"]
        for teamNum in range(2):
            team=player_game_stats[teamNum]
            print(team)
            statistics=player_game_stats[teamNum]
            stats=statistics["statistics"]
            for stat in stats:
                if stat["name"]=="defensive":
                    athletes=stat["athletes"]
                    for athlete in athletes:
                        player=athlete.get("athlete",{})
                        player_id=player.get("id","No ID Found")
                        player_position=get_player_position(player_id)
                        if player_position=="QB":
                            player_name=player.get("displayName","Unknown")  
                            player_stats=athlete.get("stats",{})
                            game_message=game_message + str(f"{player_name} had {player_stats[0]} tackle! Congrats to!")
                            tackles= tackles+int(player_stats[0])
        if tackles==0:
            return (f". There were no QB tackles.")
        elif tackles>0:
            return (f" {game_message}")
    else: return (f" Game has no stats so far.")


def get_json_response(url):
    response=requests.get(url)
    if response.status_code==200:
        data=response.json()
        return data
    else: 
        print(f"{url} has failed.")
        return {}
    

QB_Tackles_In_Game("401772861")