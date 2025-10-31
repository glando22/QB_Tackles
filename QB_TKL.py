import requests
import json


# QB total tackles 
def QB_Season_Total():
    season_total_url="https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/statistics/byathlete?region=us&lang=en&contentorigin=espn&isqualified=false&category=defense&position=8"
    response=requests.get(season_total_url)

    if response.status_code==200:
        espn_raw=response.json()
        print("Total QB Tackles")
        print("----------------")
        athletes=espn_raw["athletes"]
        for athlete in athletes:
            player=athlete["athlete"]
            player_name=player["displayName"]
            player_team=player["teamName"]
            for category in athlete["categories"]:
                if category["name"]=="defensive":
                    player_tkl=category.get("totals",[])[2]
            print(f"{player_name}, {player_team}, {player_tkl}")
    else: print("QB Season Total Fail")
    print()
# Score Board
def scoreboard():
    while True:
        try:
            week = int(input("Enter an NFL week (1–18): "))
            if 1 <= week <= 18:
                print()
                print(f"Quarterback Tackles for Week {week}")
                print("---------------------------------")
                break
            else:
                print("Please enter a number between 1 and 18.")
        except ValueError:
            print("That's not a valid number. Try again.")
    scoreboard_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?week="+str(week)
    response_scoreboard=requests.get(scoreboard_url)

    if response_scoreboard.status_code==200:
        scoreboard_raw=response_scoreboard.json()
        games=scoreboard_raw["events"]
        for game in games:
            game_id=game["id"]
            game_name=game["name"]
            QB_Tackles_In_Game(game_id,game_name)
    else: print("FAIL")

# Previous week QB tackles
def QB_Tackles_In_Game(gameId,game_name):
    game_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="+str(gameId)
    response_game=requests.get(game_url)
    game_message=""
    if response_game.status_code==200:
        game_raw=response_game.json()
        boxscore=game_raw["boxscore"]
        if "players" in boxscore:
            player_game_stats=boxscore["players"]
            tackles=0
            for teamNum in range(2):
                team=player_game_stats[teamNum]
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
                                player_stats=athlete.get("stats",{})
                                game_message=game_message+ str(f"{player.get("displayName","Unknown")} had {player_stats[0]} tackle!")
                                tackles= tackles+int(player_stats[0])
            if tackles==0:
                print(f"{game_name}. There were no QB tackles.")
            elif tackles>0:
                print(f"{game_name}. {game_message}")
        else: print(f"{game_name}. Game has no stats so far.")
                        
    else: print("FAIL")

def get_player_position(playerId):
    player_curl=(f"http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{playerId}?lang=en&region=us")
    player=requests.get(player_curl)
    if player.status_code==200:
        player_raw=player.json()
        position=player_raw["position"]
        player_position=position["abbreviation"]
        return player_position
    else: print("Player Curl Fail")
QB_Season_Total()
scoreboard()