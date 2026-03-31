# dashboard.py
import streamlit as st
from data_loader import load_week
from aggregator import aggregate_season

st.set_page_config(page_title="QB Tackle Tracker", layout="wide")

st.title("🏈 QB Tackle Tracker Dashboard")

page = st.sidebar.selectbox(
    "Navigate",
    ["Weekly Report", "Season Leaderboards", "Team Profiles", "Rivalries"]
)

qb_stats, owner_stats = aggregate_season()

# -------------------------
# WEEKLY REPORT
# -------------------------
if page == "Weekly Report":
    st.header("Weekly Tackle Report")

    week = st.selectbox("Select Week", list(range(1, 19)))
    data = load_week(week)

    if not data:
        st.warning("No data for this week.")
    else:
        st.subheader(f"Tackles in Week {week}")
        st.dataframe(data)

# -------------------------
# SEASON LEADERBOARDS
# -------------------------
elif page == "Season Leaderboards":
    st.header("Season Leaderboards")

    st.subheader("Top QBs by Tackles")
    qb_table = [
        {
            "QB": v["name"],
            "Team": v["team"],
            "Tackles": v["tackles"],
            "Impact Wins": v["impact_wins"],
            "Still Lost": v["still_lost"],
        }
        for v in qb_stats.values()
    ]
    st.dataframe(qb_table)

    st.subheader("Top Owners by Tackles For")
    owner_table = [
        {
            "Owner": k,
            "Team": v["team_name"],
            "Tackles For": v["tackles_for"],
            "Impact Wins": v["impact_wins"],
        }
        for k, v in owner_stats.items()
    ]
    st.dataframe(owner_table)

# -------------------------
# TEAM PROFILES
# -------------------------
elif page == "Team Profiles":
    st.header("Team Profiles")

    owner = st.selectbox("Select Owner", list(owner_stats.keys()))
    stats = owner_stats[owner]

    st.subheader(f"{owner} — {stats['team_name']}")
    st.json(stats)

# -------------------------
# RIVALRIES
# -------------------------
elif page == "Rivalries":
    st.header("Rivalry Analyzer")

    owners = list(owner_stats.keys())
    a = st.selectbox("Owner A", owners)
    b = st.selectbox("Owner B", owners)

    st.write("Coming soon: head-to-head tackle analysis!")