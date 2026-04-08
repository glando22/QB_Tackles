import requests
import json
from pathlib import Path


class League:
    # This function initializes the league object, which will hold all the relevant data about the league, including members, QBs, and tackle events. It also calls the function to load league members from Sleeper.
    def __init__(self):
        self.league_id = LEAGUE_ID

        # registries
        self.league_members = {}  # display_name → LeagueMember
        self.roster_id_map = {}   # roster_id → LeagueMember
        self.user_id_map = {}     # user_id → LeagueMember
        self.qbs = []             # sleeper_id → Quarterback
        self.tackle_events = []   # list of Tackle objects
        self.league_members_list=[] 
        self.tackle_keys = set()

        # load Sleeper data and populate members
        self.load_league_members()
        self.export_league_members()
        self.placeholder=LeagueMember("-1", "Placeholder Member", "Placeholder Team", "-1")

        # load current tackle data from files if it exists.
        self.load_current_tackle_data()

    def export_league_members(league, filename="league_members.json"):
        members_list = [
            member.to_dict()
            for member in league.league_members.values()
        ]

        with open(filename, "w") as f:
            json.dump(members_list, f, indent=4)
  
    def compute_weekly_impact(self,week,year):
        for tackle in self.tackle_events:
            if tackle.week != week or tackle.impact !="NONE":
                continue
            # Recalculate impact based on current points for and against


            tackle_for_points = sum(t.points for t in tackle.owner.tackles_for if t.week == week and t.year == year)
            team_points = tackle.team_points
            tackle_against_points = sum(t.points for t in tackle.opponent_owner.tackles_for if t.week == week and t.year == year)
            opp_points = tackle.opp_points
            diff = team_points - opp_points- tackle_against_points
            if diff > 0:
                tackle.impact = "No affect"
            elif diff + tackle_for_points > 0:
                tackle.impact = "Win"
            else:
                tackle.impact = "LMAOOO STILL LOST"

    def get_member_by_id(self,user_id):
        return self.user_id_map.get(user_id,self.placeholder)
    
    # This function loads the league members from the Sleeper API and populates the league's registry of members. It retrieves both the user information and roster information to create LeagueMember objects and map roster IDs to owners.
    def load_league_members(self):       
        sleeper_league_members_url=(f"http://api.sleeper.app/v1/league/{LEAGUE_ID}/users")
        sleeper_users=get_json_response(sleeper_league_members_url)
        #URL for all Sleeper Rosters
        rosters_url=(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/rosters")
        sleeper_rosters=get_json_response(rosters_url)

        for user in sleeper_users:
            display_name=user['display_name']
            user_id=user['user_id']
            team_name=user.get('metadata').get('team_name',f'{display_name}')
            roster_id=League.owner_to_roster_id(user_id,sleeper_rosters)
            league_member=LeagueMember(user_id,display_name,team_name,roster_id)
            self.user_id_map[user_id] = league_member
            self.league_members[league_member.display_name]=league_member
            self.roster_id_map[roster_id]=league_member
            self.league_members_list.append(f'{display_name}/{team_name}')
        
        


    def placeholder_member(self):
        return self.placeholder
    
    def load_current_tackle_data(self):
        year="2024"
        for week in range(1, 19):
            file_path = Path (f"data/week_{week}_{year}_tackles.json")
            if not file_path.exists():
                continue

            print(f"Loading tackle data from {file_path}...")

            with open(file_path, "r") as f:
                week_tackles = json.load(f)

            for tackle_dict in week_tackles:
                tackle_event = Tackle.from_dict(tackle_dict, self)
                self.tackle_events.append(tackle_event)
                self.tackle_keys.add(tackle_event.key())
                tackle_event.qb.record_tackle(tackle_event)
                
            



    # This function takes an owner_id and a list of sleeper rosters, and returns the roster_id associated with that owner_id. 
    def owner_to_roster_id(owner_id,sleeper_rosters):
        for roster in sleeper_rosters:
            if roster.get("owner_id")==owner_id:
                return roster.get("roster_id")

    # This function creates a Quarterback object for a given QB and adds it to the league's registry of QBs. If the QB already exists in the registry, it simply returns the existing object instead of creating a new one.
    def create_qb(self,espn_id,name,nfl_team,sleeper_id):
        # If QB already exists, return it
        qb=next((qb for qb in self.qbs if qb.espn_id == espn_id), None)
        if qb is not None:
            return qb
        qb=Quarterback(espn_id,name,nfl_team,sleeper_id)
        self.qbs.append(qb)
        return qb
    
    # This function creates a Tackle object for a given QB tackle event and adds it to the league's list of tackle events. It also updates the relevant QB's tackle count for the season.
    def record_tackle(self, qb, owner, opponent_owner, game_id, week,year, count,points,impact,team_points,opp_points):
        key=(qb.espn_id, game_id, week, year)
        if key in self.tackle_keys:
            print(f"Tackle event for QB {qb.name} in game {game_id} week {week} already recorded. Skipping duplicate.")
            return  # Tackle event already recorded, skip to avoid duplicates
        tackle_event = Tackle(qb, owner, opponent_owner, game_id, week,year, count,points,impact,team_points,opp_points)
        self.tackle_events.append(tackle_event)
        qb.record_tackle(tackle_event)

        self.tackle_keys.add(key)


    # This function outputs the tackle events for a given week, along with the impact of each tackle on the league and the relevant owners. It also includes special handling for free agents and bye weeks.
    def output_week_tackles(self,week,year):
        week_tackles = [t for t in self.tackle_events if t.week == week and t.year == year]
        
        print(f"QB Tackles for Week {week}, {year}")
        print("-------------------------")
        print(f"There were {len(week_tackles)} QB tackles in Week {week}, {year}.")
        
        for tackle in week_tackles:
            if tackle.week != week or tackle.year != year:
                continue
            if tackle.impact=="Free Agent":
                impact_message = f"{tackle.qb.name}, {tackle.qb.nfl_team} had {tackle.count} tackle(s) but is a free agent, so their tackles had no impact on the league."
                print(impact_message)
                continue
            if tackle.impact=="Bye Week":
                impact_message=f"Sadly {tackle.owner.display_name} had a bye week, so {tackle.qb.name}'s tackles were wasted. No points for {tackle.owner.display_name}!"
                print(impact_message)
                continue
            elif tackle.impact=="Benched":
                impact_message=f"Stupidly, {tackle.owner.display_name} benched {tackle.qb.name}. No points!"
            elif tackle.impact=="No affect":
                impact_message=f"{tackle.owner.display_name} would've won without {tackle.qb.name}'s tackle."
            elif tackle.impact=="Win":
                impact_message=f"Thanks to this tackle, {tackle.owner.display_name} gets the W over {tackle.opponent_owner.display_name}!."
            elif tackle.impact=="LMAOOO STILL LOST":
                impact_message=f"Even with this tackle, {tackle.owner.display_name} still lost to {tackle.opponent_owner.display_name}. Oof."
            message = (f"{tackle.qb.name}, {tackle.qb.nfl_team} had {tackle.count} tackle(s) for {tackle.owner.display_name} in their matchup against {tackle.opponent_owner.display_name}. {impact_message}")
            print(message)

    def output_season_tackles(self):
        print("Season QB Tackles")
        print("-----------------")
        print(f"There were {sum(t.count for t in self.tackle_events)} total QB tackles in the season!")
        for qb in self.qbs:
            print(f"{qb.name}, {qb.nfl_team}: {sum(t.count for t in self.tackle_events if t.qb == qb)}")
        
        print(f"Out of {sum(t.count for t in self.tackle_events)} tackles, the league scored {sum(t.points for t in self.tackle_events)} points.")
        print(f"{sum(1 for t in self.tackle_events if t.impact=='Win')} that directly resulted in wins for the tackle owner.\n{sum(1 for t in self.tackle_events if t.impact=='LMAOOO STILL LOST')} that still resulted in losses.\n{sum(1 for t in self.tackle_events if t.impact=='No affect')} that had no affect on the outcome of the matchup.")
        print(f"{sum(1 for t in self.tackle_events if t.impact=='Benched')} tackles were made by benched QBs that had no impact on the league.\n{sum(1 for t in self.tackle_events if t.impact=='Bye Week')} tackles that were wasted due to bye weeks.")
        print(f"{sum(1 for t in self.tackle_events if t.impact=='Free Agent')} tackles were by free agents that had no impact on the league.")


   

class LeagueMember:
    # This class represents a member of the fantasy football league. It stores the user's ID, display name, team name, roster ID, and their tackle counts for and against them. The class also includes a method to display the team information.
    def __init__(self,user_id,display_name,team_name,roster_id):
        self.user_id=user_id
        self.display_name=display_name
        self.team_name=team_name
        self.tackles_for=[]
        self.tackles_against=[]
        self.roster_id=roster_id

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "team_name": self.team_name,
            "roster_id": self.roster_id
        }
    
    # This function just print the team info for the league member.
    def display_team(self):
        print(f"{self.display_name}'s team, {self.team_name}, has a Sleeper ID of {self.user_id}. Roster ID is {self.roster_id}.")
    

class Quarterback:
    # This class represents a quarterback. It stores the player's ESPN ID, name, NFL team, Sleeper ID, and a list of their tackle events. The class also includes methods to record a tackle event, calculate the total tackles for the season, and provide a string representation of the quarterback.
    def __init__(self, espn_id, name, nfl_team,sleeper_id):
        self.espn_id = espn_id
        self.name = name
        self.nfl_team = nfl_team
        self.sleeper_id = sleeper_id
        self.tackles = []   # list of Tackle dictionaries
        self.season_tackles=0
    # This function takes a tackle event and adds it to the quarterback's list of tackles.
    def record_tackle(self, tackle_event):
        self.tackles.append(tackle_event)
    # This function calculates the total number of tackles for the quarterback by summing the count of each tackle event in their list of tackles.
    def total_tackles(self):
        return sum(t.count for t in self.tackles)
    
    def to_dict(self):
        return {
            "espn_id": self.espn_id,
            "sleeper_id": self.sleeper_id,
            "name": self.name,
            "nfl_team": self.nfl_team,
        }

    def __repr__(self):
        return f"<QB {self.espn_id}, {self.name} ({self.nfl_team}) Tackles={self.total_tackles()}>. Sleeper ID: {self.sleeper_id}"
            

class Tackle:
    # This class represents a tackle event. It stores the quarterback involved in the tackle, the owner of the quarterback, the opponent owner, the game ID, the week of the season, the count of tackles, the points awarded for the tackle, and the impact of the tackle on the league.
    def __init__(self, qb, owner, opponent_owner, game_id, week,year, count,points,impact,team_points,opp_points):
        self.qb = qb
        self.owner = owner
        self.opponent_owner = opponent_owner
        self.game_id = game_id
        self.week = week
        self.year=year
        self.count = count
        self.points=points
        self.impact=impact
        self.team_points=team_points
        self.opp_points=opp_points
        owner.tackles_for.append(self) 
        opponent_owner.tackles_against.append(self)
        # print(self.__repr__())

    # return dictionary representation of the tackle event for saving to JSON file. Note that we convert the QB object to just the name for easier readability in the saved files.
    def to_dict(self):
        return {
            "qb": self.qb.to_dict(),
            "owner": self.owner.to_dict(),
            "opponent": self.opponent_owner.to_dict(),
            "week": self.week,
            "year": self.year,
            "game_id": self.game_id,
            "count": self.count,
            "points": self.points,
            "impact": self.impact,
            "team_points": self.team_points,    
            "opp_points": self.opp_points
        }
    @classmethod
    def from_dict(cls, data, league):
        qb_data = data["qb"]
        qb = league.create_qb(
            qb_data["espn_id"],
            qb_data["name"],
            qb_data["nfl_team"],
            qb_data["sleeper_id"]
        )

        owner = league.get_member_by_id(data["owner"]["user_id"])
        opponent = league.get_member_by_id(data["opponent"]["user_id"])

        return cls(
            qb=qb,
            owner=owner,
            opponent_owner=opponent,
            game_id=data["game_id"],
            week=data["week"],
            year=data["year"],
            count=data["count"],
            points=data["points"],
            impact=data["impact"],
            team_points=data["team_points"],
            opp_points=data["opp_points"]
        )

    def key(self):
        return (self.qb.espn_id, self.game_id, self.week,self.year)

    def __repr__(self):
        return (f"<Tackle QB={self.qb.name}, "
                f"Owner={self.owner.display_name}, "
                f"Against={self.opponent_owner.display_name}, "
                f"Week={self.week}, Year={self.year}, Count={self.count}, "
                f"Points={self.points}, Impact={self.impact}"
                )

# These are the league constants that are specific to my league. You will need to change the LEAGUE_ID and POINTS_PER_TACKLE to match your league's settings.
LEAGUE_ID="1257089031162830848"
POINTS_PER_TACKLE=100
ADMINPASSWORD="212212"

# This function prints the total number of QB tackles for the season by calling the ESPN Season Statistic API endpoint for QBs. It also prints out the individual tackle counts for each QB and their respective teams.
def QB_Season_Total():
    # URL of season long data filtered to QBs 
    season_total_url="https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/statistics/byathlete?region=us&lang=en&contentorigin=espn&isqualified=false&category=defense&position=8&seasontype=2"
    espn_raw=get_json_response(season_total_url)
    total_tkl=0
    print("Total QB Tackles")
    print("----------------")
    athletes=espn_raw["athletes"]
    for athlete in athletes:
        for category in athlete["categories"]:
            if category["name"]=="defensive":
                player_tkl=category.get("totals",[])[2]
        if int(player_tkl)>0:  
                player=athlete["athlete"]
                player_name=player["displayName"]
                if player_name=="Taysom Hill":
                    continue
                player_team=player["teamName"]
                total_tkl=int(player_tkl)+total_tkl
                print(f"{player_name}, {player_team}, {player_tkl}")
    print()
    print(f"There were {total_tkl} total QB tackles in the season!")




# This function is the main function that processes the QB tackles for a given week. It retrieves the list of games for the week from ESPN.
# Calls the function to get the QB tackles for each game, and then records the tackle events in the league. 
# It also includes functionality to save the tackle events to a file and to skip processing if the data has already been saved.
def scoreboard(week,year,save):
    overwrite=""
    #check that the week has already been saved or not. If so, skip API calls and just read from file.
    file_path = Path(f"data/week_{week}_{year}_tackles.json")
    if file_path.exists():
        if save==1:
            overwrite = get_user_input_from_options(f"Week {week}, {year} has already been processed and saved to {file_path}. Do you want to overwrite it?", ["Yes", "No"])                                                 
        if overwrite.lower() not in ["y", "yes"]: 
            league.output_week_tackles(week,year)
            return
    else: 
        if save==0:
            print(f"Data for week {week}, {year} doesn't exist yet. Contact your league manager to update the data.")
            return
   

    # url for list of every game in a given week
    # scoreboard_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?week="+str(week)+"&year="+str(year)
    scoreboard_url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{year}/types/2/weeks/{week}/events"
    scoreboard_raw=get_json_response(scoreboard_url)
    # games=scoreboard_raw["events"]
    games=scoreboard_raw["items"]

    
    

    # URL for all Sleeper matchups in a given week
    sleeper_matchup_url=(f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/matchups/{week}")
    sleeper_matchups=get_json_response(sleeper_matchup_url)
    #Url for all Sleeper Users
    league_member_url=(f"http://api.sleeper.app/v1/league/{LEAGUE_ID}/users")
    league_users=get_json_response(league_member_url)
    for game in games:
        game_id=game["$ref"].split("/")[-1].split("?")[0]
        game_name=get_game_name(game_id)
        # game_name=game["name"]
        print(f"Processing {game_name}, {game_id}...{games.index(game)+1}/{len(games)}.")
        # now call to specific game stats page
        sleeper_stats_list=QB_Tackles_In_Game(game_id,game_name,sleeper_matchups)
        for sleeper_stats in sleeper_stats_list:
            if sleeper_stats and sleeper_stats['count'] > 0:
                print(f"{sleeper_stats['qb'].name} had a tackle. Recording tackle event...")
                league.record_tackle(sleeper_stats['qb'],sleeper_stats['owner'],sleeper_stats['opponent'],game_id,week,year,sleeper_stats['count'],sleeper_stats['points'],sleeper_stats['impact'],sleeper_stats['team_points'],sleeper_stats['opp_points'])
    league.compute_weekly_impact(week,year)
    league.output_week_tackles(week,year)
    save_tackle_events_to_file(week,year)

def get_game_name(game_id):
    game_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="+str(game_id)
    game_raw=get_json_response(game_url)
    return game_raw["header"]["competitions"][0]["competitors"][0]["team"]["displayName"]+" vs. "+game_raw["header"]["competitions"][0]["competitors"][1]["team"]["displayName"]

# This function takes a game ID and retrieves the boxscore data for the game from ESPN. 
# It then processes the defensive statistics to find any tackles made by QBs. If it finds any, it creates a QB object and calls the sleeper_tackle function to determine the impact of the tackle on the league. 
# It returns a dictionary with the relevant information about the tackle event.
def QB_Tackles_In_Game(game_id,game_name,sleeper_matchups):
    sleeper_stats_list=[]
    game_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="+str(game_id)
    game_raw=get_json_response(game_url)
    boxscore=game_raw["boxscore"]
    tackles=0
    if "players" in boxscore:
        player_game_stats=boxscore["players"]
        for teamNum in range(2):
            team=player_game_stats[teamNum]
            statistics=player_game_stats[teamNum]
            stats=statistics["statistics"]
            for stat in stats:
                if stat["name"]!="defensive":
                    continue
                athletes=stat["athletes"]
                for athlete in athletes:
                    player=athlete.get("athlete",{})
                    player_id=player.get("id","No ID Found")
                    player_position=get_player_position(player_id)
                    if player_position=="QB":
                        stats=athlete.get("stats",{})
                        num_tackles=int(stats[0])
                        if num_tackles>0:
                            qb_name=player.get("displayName","Unknown")
                            sleeper_id=find_sleeper_player(qb_name)
                            if sleeper_id is None:
                                continue
                            qb=league.create_qb(player_id,qb_name,team["team"]["displayName"],sleeper_id)
                            sleeper_stats=sleeper_tackle(qb,sleeper_matchups,num_tackles)
                            sleeper_stats['qb']=qb
                            sleeper_stats['count']=num_tackles
                            sleeper_stats_list.append(sleeper_stats)

    return sleeper_stats_list 

# This function retrieves the current week of the NFL season from ESPN. It also prints out the current week, year, and season type (preseason, regular season, or postseason) for the user's reference.
def get_current_week():
    current_week_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    current_week_raw=get_json_response(current_week_url)
    current_week= current_week_raw["week"]["number"]         
    current_year=current_week_raw["season"]["year"]
    current_season_type=current_week_raw["season"]["type"]
    if current_season_type==1:
        current_season_type="Preseason"
    elif current_season_type==2:
        current_season_type=="Regular Season"
    elif current_season_type==3:
        current_season_type="Postseason"
        
    print(f"It is currently week {current_week} of the {current_year} {current_season_type}.")
    return current_week  

# This function takes a week number and saves the tackle events for that week to a JSON file. 
def save_tackle_events_to_file(week,year):
    data=[]
    for tackle in league.tackle_events:
        if tackle.week != week or tackle.year!=year:
            continue    
        data.append(tackle.to_dict())
    with open(f"data/week_{week}_{year}_tackles.json", "w") as f:
        json.dump(data, f, indent=4)

     

# This function takes a player's name and searches through the sleeper_players.json file to find the corresponding Sleeper ID.
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
            if player_info.get("full_name")==player_name and "QB" in player_info.get("fantasy_positions",""):
                return player_id
        return None  # Player not found
    except Exception as e:
        print("Error reading sleeper_players.json:", e)
        return None

# This function converts the number of tackles into points based on the league's scoring settings and determines the impact of the tackle on the league.
# It checks if the QB is a free agent, if they had a bye week, if they were benched, and then calculates the impact based on the point difference between the two teams in the matchup.
def sleeper_tackle(qb, sleeper_matchups, num_tackles):
    sleeper_stats = {}
    qb_id = qb.sleeper_id
    placeholder_member=league.placeholder_member()
    # SAFE DEFAULTS
    impact = "NONE"
    points = 100 * num_tackles
    owner = placeholder_member
    opponent_owner = placeholder_member
    team_sleeper_points=0
    opp_sleeper_points=0

    for roster in sleeper_matchups:
        if qb_id in roster.get("players", []):
            roster_id=roster.get("roster_id")
            owner = league.roster_id_map.get(roster_id)

            opponent_roster_id = find_opponent_roster(roster_id, sleeper_matchups)
            opponent_owner = league.roster_id_map.get(opponent_roster_id)

            
            # Bye week
            if opponent_owner is None:
                impact = "Bye Week"
                points = 0
                opponent_owner = placeholder_member

                break

            team_sleeper_points = get_points_from_roster_id(roster_id, sleeper_matchups)
            opp_sleeper_points = get_points_from_roster_id(opponent_roster_id, sleeper_matchups)

            # Benched QB
            if qb_id not in roster.get("starters", []):
                impact = "Benched"
                points = 0
                break

            
            

    if owner == placeholder_member:
        impact = "Free Agent"
        points = 0
        owner = placeholder_member
        opponent_owner = placeholder_member

   
    sleeper_stats['qb'] = qb
    sleeper_stats['owner'] = owner
    sleeper_stats['opponent'] = opponent_owner
    sleeper_stats['points'] = points
    sleeper_stats['impact'] = impact
    sleeper_stats['count'] = num_tackles
    sleeper_stats['team_points'] = team_sleeper_points
    sleeper_stats['opp_points'] = opp_sleeper_points

    return sleeper_stats

# This function takes a roster_id and the sleeper_matchups data, and returns the points scored by that roster in the matchup.
def get_points_from_roster_id(roster_id, sleeper_matchups):
    for roster in sleeper_matchups:
        if roster["roster_id"] == roster_id:
            return roster.get("points", 0)
    return None  # roster not found
            
# This function takes a roster_id and the sleeper_matchups data, and returns the roster_id of the opponent in the matchup.
def find_opponent_roster(roster_id, sleeper_matchups):
    matchup_id = None
    # Step 1: find my matchup_id
    for roster in sleeper_matchups:
        if roster["roster_id"] == roster_id:
            matchup_id = roster.get("matchup_id")
            break
    if matchup_id is None:
        return None  # not found or bye week
    # Step 2: find the opponent with the same matchup_id
    for roster in sleeper_matchups:
        if roster.get("matchup_id") == matchup_id and roster["roster_id"] != roster_id:
            return roster["roster_id"]
    return None  # no opponent found
    
# This function takes an ESPN Player ID and returns the players' position from ESPN
def get_player_position(playerId):
    player_curl=(f"http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{playerId}?lang=en&region=us")
    player_raw=get_json_response(player_curl)
    position=player_raw["position"]
    player_position=position["abbreviation"]
    return player_position

# This function is a one time call to get list of all Sleeper players and save to sleeper_players.json.
def sleeper_players():
    player_url="https://api.sleeper.app/v1/players/nfl"
    player_list=get_json_response(player_url)
    with open('sleeper_players.json','w') as f:
        json.dump(player_list,f,indent=4)

# This function takes a roster_id and the list of sleeper rosters, and returns the user_id of the owner associated with that roster_id.   
def get_user_sleeper_id(roster_id,sleeper_rosters):
    for rosters in sleeper_rosters:
        if rosters.get("roster_id")==roster_id:
            return rosters.get("owner_id")  

# This function prompts the user to input an NFL week number (1-18) or "all" to process all weeks. 
# It validates the input and calls the scoreboard function for the specified week(s). 
# It also includes an option to exit the program.
def week_input(user_role,save, year="2025"):
    # User input for an NFL week

    while True:
        try:
            week = input("Enter an NFL week (1–18): ")
            if week.lower() in ('opt','q','quit'):
                print("Exiting program.")
                exit()
            if week == "all":
                print()
                print("Looping through all weeks and saving to files.")
                for i in range(1,19):
                    scoreboard(i, year, save)
                return
            if week == "current":
                week=get_current_week()
                print(f"Processing current week, week {week}...")
                scoreboard(week, year, save)
                return
            week = int(week)
            if 1 <= week <= 18:
                print()
                print(f"Quarterback Tackles for Week {week}, {year}")
                print("--------------------------------")
                scoreboard(week, year, save)
                return
                
            
            else:
                print("Please enter a number between 1 and 18.")
        except ValueError:
            print("That's not a valid number. Try again.")

def get_user_input_from_options(prompt, options):
    print(prompt)
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")

    while True:
        choice = input("Choose an option: ")
        if choice.lower() in ('opt','q','quit'):
            print("Exiting program.")
            exit()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        if choice.lower() in [option.lower() for option in options]:
            return choice
        print("Invalid choice, try again.")

def qb_tkl():
    user=get_user_input_from_options("Welcome to the QB Tackle Tracker! Who are you?", league.league_members_list)
    user_role = get_user_input_from_options("Select your role:", ["League Member", "League Admin"])
    save=0
    if user_role == "League Admin":
        if input("Password: ") == ADMINPASSWORD:  # Replace with your actual admin password
            print("Access granted. You can view and update tackle events.")
            admin_ops = get_user_input_from_options("View Only or Save:", ["View Only", "Update"])
            if admin_ops == "Update":
                save = 1
        else:
            print("Access denied. You can only view tackle events.")
            user_role = "League Member"  # Downgrade to League Member if password is incorrect
    elif user_role == "League Member":
        print("You have selected League Member. You can view weekly tackle events and season totals.")
    keep_going = "Yes"
    while keep_going=="Yes":    
        operation = get_user_input_from_options("View Weekly Tackles or Season Totals?", ["Weekly Tackles", "QB Season Totals", "League Member Profiles"])
        if operation == "QB Season Totals":
            QB_Season_Total()
            league.output_season_tackles()
        elif operation == "League Member Profiles": 
            member_profile_input = get_user_input_from_options("Select a league member to view their profile:", league.league_members_list)
            member_profile(member_profile_input.split("/")[0])  # Extract display name from "Display Name/Team Name" format  
        elif operation == "Weekly Tackles":
            week_input(user_role, save,year="2024")
        keep_going = get_user_input_from_options("Do you want to perform another operation?", ["Yes", "No"])
        
def member_profile(display_name):
    points_for=0
    points_against=0
    member=league.league_members.get(display_name)
    print(f"Profile for {member.display_name}, owner of {member.team_name}.")
    print(f"Tackles for:")
    for tackle in member.tackles_for:
        print(f"{tackle.qb.name} had {tackle.count} tackle(s) for {member.display_name} in week {tackle.week} against {tackle.opponent_owner.display_name}. Impact: {tackle.impact}")
        points_for+=tackle.points
    print(f"Total Tackles for: {len(member.tackles_for)}. Total points for: {points_for}")
    print(f"Tackles against:")
    for tackle in member.tackles_against:
        print(f"{tackle.qb.name} had {tackle.count} tackle(s) against {member.display_name} in week {tackle.week} by {tackle.owner.display_name}. Impact: {tackle.impact}")
        points_against+=tackle.points
    print(f"Total Tackles against: {len(member.tackles_against)}. Total points against: {points_against}")
       
            
# This function takes a URL, makes a GET request to the URL, and returns the JSON response if the request is successful. If the request fails, it prints an error message and returns an empty dictionary.
def get_json_response(url):
    response=requests.get(url)
    if response.status_code==200:
        data=response.json()
        return data
    else: 
        print(f"{url} has failed.")
        return {}


league = League()
qb_tkl()


