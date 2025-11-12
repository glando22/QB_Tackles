import requests
import json
import time 

# QB total tackles 
# This prints a list of the QBs that have made a tackle during the season
def QB_Season_Total():
    # URL of season long data filtered to QBs 
    season_total_url="https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/statistics/byathlete?region=us&lang=en&contentorigin=espn&isqualified=false&category=defense&position=8"

    espn_raw=get_json_response(season_total_url)
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
    print()


# Score Board
def scoreboard(week,save):
    # url for list of every game in a given week
    scoreboard_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?week="+str(week)
    scoreboard_raw=get_json_response(scoreboard_url)
    games=scoreboard_raw["events"]
    #Sleeper League ID
    league_id="1257089031162830848"
    # URL for all Sleeper matchups in a given week
    sleeper_matchup_url=(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}")
    sleeper_matchups=get_json_response(sleeper_matchup_url)
    #URL for all Sleeper Rosters
    rosters_url=(f"https://api.sleeper.app/v1/league/1257089031162830848/rosters")
    sleeper_rosters=get_json_response(rosters_url)
    #Url for all Sleeper Users
    league_member_url=(f"http://api.sleeper.app/v1/league/{league_id}/users")
    league_users=get_json_response(league_member_url)
    with open(f"QB_TKL_Week_{week}.txt","w") as file:
                file.write(f"Week {week} Stats\n")
    for game in games:
        game_id=game["id"]
        game_name=game["name"]
        # now call to specific game stats page
        game_message=QB_Tackles_In_Game(game_id,game_name,sleeper_matchups,league_users,sleeper_rosters)
        if save:
            with open(f"QB_TKL_Week_{week}.txt","a") as file:
                file.write(f"{game_message}\n")
            print(game_message)
        else: print(game_message)
# Week specific QB tackles
def QB_Tackles_In_Game(gameId,game_name,sleeper_matchups,sleeper_users,sleeper_rosters):
    game_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="+str(gameId)
    game_message=""
    game_raw=get_json_response(game_url)
    boxscore=game_raw["boxscore"]
    position_cache={}
    tackles=0
    if "players" in boxscore:
        player_game_stats=boxscore["players"]
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
                            player_name=player.get("displayName","Unknown")
                            sleeper_owner_name=sleeper_owner(player_name,sleeper_matchups,sleeper_users,sleeper_rosters)
                            # sleeper_player_id=find_sleeper_player(player_name)
                            # if sleeper_player_id:
                            #     sleeper_team_id=player_on_roster(sleeper_player_id)
                            #     sleeper_team=sleeper_owner(sleeper_team_id)
                            # else: sleeper_team="Unknown"
                            player_stats=athlete.get("stats",{})
                            game_message=game_message + str(f"{player_name} had {player_stats[0]} tackle! Congrats to {sleeper_owner_name}!")
                            tackles= tackles+int(player_stats[0])
        if tackles==0:
            return (f"{game_name}. There were no QB tackles.")
        elif tackles>0:
            return (f"{game_name}. {game_message}")
    else: return (f"{game_name}. Game has no stats so far.")


# Takes an ESPN Player ID and returns the players' position from ESPN
def get_player_position(playerId):
    player_curl=(f"http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{playerId}?lang=en&region=us")
    player_raw=get_json_response(player_curl)
    position=player_raw["position"]
    player_position=position["abbreviation"]
    return player_position

# One time call to get list of all Sleeper players and save to sleeper_players.json
def sleeper_players():
    player_url="https://api.sleeper.app/v1/players/nfl"
    player_list=get_json_response(player_url)
    with open('sleeper_players.json','w') as f:
        json.dump(player_list,f,indent=4)

# Take a player's name and search through sleeper_players.json to find their sleeper ID
def find_sleeper_player(player_name):
    file_path = 'sleeper_players.json' 
    try:
        # Open the JSON file in read mode ('r') using a 'with' statement
        # The 'with' statement ensures the file is properly closed even if errors occur
        with open(file_path, 'r') as file:
            # Load the JSON data from the file
            players = json.load(file)
        
        # Now 'data' contains the parsed JSON as a Python object
        for player_id, player_info in players.items():
            if player_info.get("full_name")==player_name:
                return player_id
                
    
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from '{file_path}'. The file might contain invalid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None

# Take the owner_id and convert it to the Owner's username
def sleeper_owner(player_name,sleeper_matchups,sleeper_users,sleeper_rosters):
    player_id=find_sleeper_player(player_name)
    roster_id=get_sleeper_matchup_roster(player_id,sleeper_matchups)  
    user_id=get_user_sleeper_id(roster_id,sleeper_rosters)
    for member in sleeper_users:
        if member.get("user_id")==user_id:
            owner_name=member.get("display_name")
            return owner_name
            
def get_user_sleeper_id(roster_id,sleeper_rosters):
    for rosters in sleeper_rosters:
        if rosters.get("roster_id")==roster_id:
            return rosters.get("owner_id")  

def user_input():
    # User input for an NFL week
    while True:
        try:
            week = input("Enter an NFL week (1–18): ")
            if week == "all":
                print()
                print("Looping through all weeks and saving to files.")
                for i in range(1,19):
                    scoreboard(i,1)
                    print(f"Week {i} Complete.")
                break
            week = int(week)
            if 1 <= week <= 18:
                print()
                print(f"Quarterback Tackles for Week {week}")
                print("--------------------------------")
                scoreboard(week,1)
                break
            
            else:
                print("Please enter a number between 1 and 18.")
        except ValueError:
            print("That's not a valid number. Try again.")

# Search for a player on any of the leagues rosters (in the starters list)
def get_sleeper_matchup_roster(player_id,sleeper_matchups):
    for roster in sleeper_matchups:
        if player_id in roster.get("starters",[]):
            team_id=roster.get("roster_id")
            return team_id
            


# standardized API call structure
def get_json_response(url):
    response=requests.get(url)
    if response.status_code==200:
        data=response.json()
        return data
    else: 
        print(f"{url} has failed.")
        return {}




# Run the 2 main programs
QB_Season_Total()
user_input()
