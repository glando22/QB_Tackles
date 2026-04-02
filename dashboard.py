# dashboard.py
import streamlit as st
from data_loader import load_week
from aggregator import aggregate_season

st.set_page_config(page_title="QB Tackle Tracker", layout="wide")

st.title("🏈 QB Tackle Tracker Dashboard")

page = st.sidebar.selectbox(
    "Navigate",
    ["Weekly Report", "Season Leaderboards", "Team Profiles"]
)

qb_stats, owner_stats = aggregate_season()

# -------------------------
# WEEKLY REPORT
# -------------------------
if page == "Weekly Report":
    st.header("Weekly Tackle Report")

    week = st.selectbox("Select Week", list(range(1, 19)))
    data = load_week(week)

    weekly_table= [{
        "QB": f"{t["qb"]["name"]} - {t["qb"]["nfl_team"]}",
        "Owner": f"{t["owner"]["display_name"]} - {t["owner"]["team_name"]}",
        "Opponent": f"{t["opponent"]["display_name"]} - {t["opponent"]["team_name"]}",
        "Tackles": t["count"],
        "Impact": t["impact"],
    }
    for t in data]

    if not data:
        st.warning("There weren't any QB tackles for this week.")
    else:
        st.subheader(f"Tackles in Week {week}")
        st.dataframe(weekly_table)

# -------------------------
# SEASON LEADERBOARDS
# -------------------------
elif page == "Season Leaderboards":
    st.header("Season Leaderboards")

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

    owner = st.selectbox("Select Owner", list(owner_stats.keys()))
    stats = owner_stats[owner]

    st.subheader(f"{stats['display_name']} — {stats['team_name']}")
    st.json(stats)

# -------------------------
# RIVALRIES
# -------------------------
# elif page == "Rivalries":
#     st.header("Rivalry Analyzer")

#     owners = list(owner_stats.keys())
#     a = st.selectbox("Owner A", owners)
#     b = st.selectbox("Owner B", owners)

#     st.write("Coming soon: head-to-head tackle analysis!")
