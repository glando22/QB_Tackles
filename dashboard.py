# dashboard.py
import streamlit as st
from data_loader import load_week,load_all_weeks
from aggregator import aggregate_season
import pandas as pd

def resolve_owner(tackle):
    if tackle["owner"]["user_id"] == "-1": 
        if tackle["impact"] == "Free Agent":
            return "Free Agent QB"
        elif tackle["impact"] == "Bye":
            return "Bye Week"
    return f"{tackle["owner"]["display_name"]} - {tackle["owner"]["team_name"]}"

def resolve_opponent(tackle):
    if tackle["opponent"]["user_id"] == "-1": 
        if tackle["impact"] == "Free Agent":
            return "Free Agent QB"
        elif tackle["impact"] == "Bye Week":
            return "Bye Week"
    return f"{tackle["opponent"]["display_name"]} - {tackle["opponent"]["team_name"]}"

st.set_page_config(page_title="QB Tackle Tracker", layout="wide")

st.title("🏈 QB Tackle Tracker Dashboard")

page = st.sidebar.radio(
    "Navigate",
    ["Weekly Report", "Season Leaderboards", "Team Profiles","QB Tackle Tracker Info"]
)

results = aggregate_season()

# -------------------------
# WEEKLY REPORT
# -------------------------
if page == "Weekly Report":
    st.header("Weekly Tackle Report")
    col_yr,col_wk = st.columns(2)
    with col_yr:
        year = st.selectbox("Select Year", ["2024","2025", "2026"],width=100,index=1)  
    with col_wk:
        week = st.selectbox("Select Week", list(range(1, 19)),width=100)  
    data = load_week(week,year)
    
    
  
    weekly_table= [{
        
        "QB": f"{t["qb"]["name"]} - {t["qb"]["nfl_team"]}",
        "Owner": resolve_owner(t),
        "Opponent": resolve_opponent(t),
        "Tackles": t["count"],
        "Impact": t["impact"],
    }
    for t in data if "message" not in t]

    if not data:
        st.warning("There weren't any QB tackles for this week.")
    elif "message" in data[0] and data[0]["message"] == "This week has not happened yet!":
        st.info("This week has not happened yet! Check back once the week is over to see the tackle report.")
    else:
        st.subheader(f"Tackles in Week {week}")
        st.dataframe(weekly_table)

# -------------------------
# SEASON LEADERBOARDS
# -------------------------
elif page == "Season Leaderboards":
    st.header("Season Leaderboards")

    year = st.selectbox("Select Year", ["2024","2025", "2026","All-time"],index=1)  
    data = results["all"] if year == "All-time" else results[year]
    qb_stats = data["qb_stats"]
    owner_stats = data["owner_stats"]

    st.subheader(f"Top QBs by Tackles - Total Tackles: {sum(v['tackles'] for v in qb_stats.values())}")

    qb_table = [
        {
            "QB": v["name"],
            "Team": v["team"],
            "Tackles": v["tackles"],
            "Impact Wins": v["impact_wins"]  
        }
        for v in qb_stats.values() 
    ]
    qb_table = sorted(qb_table, key=lambda x: x["Tackles"], reverse=True)
    if qb_table:
        st.dataframe(qb_table,height="content")

    st.subheader("Top Owners by Tackles For")
    owner_table = [
        {
            "Owner": f"{v['display_name']} - {v['team_name']}",
            "Tackles For": v["tackles_for"],
            "Impact Wins": v["impact_wins"],
            "Tackles Against": v["tackles_against"]    
        }
        for k, v in owner_stats.items() if k !='-1'
    ]
    owner_table = sorted(owner_table, key=lambda x: x["Tackles For"], reverse=True)
    st.dataframe(owner_table,height="content")

# -------------------------
# TEAM PROFILES
# -------------------------
elif page == "Team Profiles":
    st.header("Team Profiles")
    year = st.selectbox("Select Year", ["2024","2025", "2026","All-time"],index=1) 
    data = results["all"] if year == "All-time" else results[year]
    qb_stats = data["qb_stats"]
    owner_stats = data["owner_stats"]

    owner_options = {
        f"{v["display_name"]} - {v["team_name"]}": k
        for k, v in owner_stats.items()
        if k != "-1"
    }

    selected_display_name = st.selectbox("Select Owner", list(owner_options.keys()))

    owner=owner_options[selected_display_name]
    stats = owner_stats[owner]
    df = [
        {
        "Label": "Tackles For",
        "Meaning": stats["tackles_for"],
        },
        {
        "Label": "Total Points For",
        "Meaning": stats["total_points_for"]
        },
        {
        "Label": "Wins Due to Tackles",
        "Meaning": stats["impact_wins"],
        },
        {
        "Label": "Tackles Against",
        "Meaning": stats["tackles_against"],
        },
        {
        "Label": "Total Points Against",
        "Meaning": stats["total_points_against"]
        },
        {
        "Label": "Losses Caused by Tackles",
        "Meaning": stats["losses"],
        },
        {
        "Label": "Tackles Left on the Bench",
        "Meaning": stats["benched"],
        },
        {
        "Label": "Tackles During a Bye",
        "Meaning": stats["bye_week"],
        },
    ]

    st.subheader(f"{stats['display_name']} — {stats['team_name']}")
    st.dataframe(df)

    if year != "All-time":
        tackles=load_all_weeks(year)
    else:        
        tackles = []
        for y in ["2024","2025","2026"]:
            tackles.extend(load_all_weeks(y)) 
    team_tackles = [t for t in tackles if "message" not in t and t["owner"]["user_id"] == owner]
    incomplete_weeks = [t for t in tackles if "message" in t]
    if len(incomplete_weeks) == 18 and year != "All-time":
        st.info("The season hasn't started yet. Check back once the season starts to see how your team is doing!")
    elif team_tackles:
        for t in team_tackles:
            if t["impact"] == "Win":
                impact_message = "This QB's extraordinary effort gave you a win that week! Congratulations!"
            elif t["impact"] == "LMAOOO STILL LOST":
                impact_message = "Despite the QB's heroic tackle and 100 bonus points, you still lost. Embarassing!"
            elif t["impact"] == "No affect":
                impact_message = "You would've won your matchup even without this QB's heroic actions! Bravo!"
            elif t["impact"] == "Benched":
                impact_message = "This QB was on your bench that week. What a blunder from the team's management!"
            elif t["impact"] == "Bye Week":
                impact_message = "You missed out on the points because you were on a bye week. Should've saved it when you needed it! Unfortunate!"


            st.info(f"During your week {t['week']} matchup against {resolve_opponent(t)}, {t['qb']['name']} ({t['qb']['nfl_team']}) made {t['count']} tackles. {impact_message}")
    else:
        st.info("Wow. No tackles for you at all this season. It must have been frustrating watching your fellow league members bask in the points and glory.")
elif page=="QB Tackle Tracker Info":
    st.header("QB Tackle Tracker Info")

    impact_table = [
    {
        "Label": "Win",
        "Meaning": "The QB tackle points flipped the outcome of the matchup in the owner's favor.",
    },
    {
        "Label": "LMAOOO STILL LOST",
        "Meaning": "You somehow still lost your matchup despite having 100 bonus points. Shame.",
    },
    {
        "Label": "No affect",
        "Meaning": "The owner would have won this matchup without the bonus points.",
    },
    {
        "Label": "Benched",
        "Meaning": "The QB was on the owner's bench and they wasted 100 points.",
    },
    {
        "Label": "Bye Week",
        "Meaning": "The QBs owner was on a Bye week so they did not get to take advantage of the tackle.",
    },
    {
        "Label": "Free Agent",
        "Meaning": "The QB was not rostered by any team when they made a tackle.",
    }
    ]

    st.dataframe(impact_table)
