class League:
    def __init__(self,league_id="1257089031162830848"):
        self.league_id = league_id

        # registries
        self.league_members = {}  # display_name → LeagueMember
        self.qbs = {}             # espn_id → Quarterback
        self.tackle_events = []   # list of Tackle objects

        # load Sleeper data and populate members
        self.load_league_members()

    # instantiate class of league members
    def load_league_members(self):
        #Url for all Sleeper Users
        sleeper_league_members_url=(f"http://api.sleeper.app/v1/league/{league_id}/users")
        sleeper_users=get_json_response(sleeper_league_members_url)
        for user in sleeper_users:
            display_name=user['display_name']
            user_id=user['user_id']
            team_name=user.get('metadata').get('team_name')
            league_member=LeagueMember(user_id,display_name,team_name)
            self.league_members[league_member.display_name]=league_member
            print(f'Loaded {display_name}. ID: {user_id}, Team Name: {team_name}')

class LeagueMember:
    def __init__(self,user_id,display_name,team_name):
        # Initialize the league member
        self.user_id=user_id
        self.display_name=display_name
        self.team_name=team_name
        self.tackles_for=0
        self.tackles_against=0

    def display_team(self):
        print(f"{self.display_name}'s team, {self.team_name}, has a Sleeper ID of {self.user_id}")
    

class Quarterback:
    def __init__(self, espn_id, name, nfl_team, sleeper_id=None, owner=None):
        self.espn_id = espn_id
        self.name = name
        self.nfl_team = nfl_team
        self.sleeper_id = sleeper_id
        self.tackles = []   # list of Tackle dictionaries
        self.season_tackles=0

    def record_tackle(self, tackle_event):
        self.tackles.append(tackle_event)

    def total_tackles(self):
        return sum(t.count for t in self.tackles)

    def __repr__(self):
        return f"<QB {self.name} ({self.nfl_team}) Tackles={self.total_tackles()}>"
            

class Tackle:
    def __init__(self, qb, qb_owner, opponent_owner, game_id, week, count):
        self.qb = qb
        self.qb_owner = qb_owner
        self.opponent_owner = opponent_owner
        self.game_id = game_id
        self.week = week
        self.count = count

    def __repr__(self):
        return (f"<Tackle QB={self.qb.name}, "
                f"Owner={self.qb_owner.display_name}, "
                f"Against={self.opponent_owner.display_name}, "
                f"Week={self.week}, Count={self.count}>")