# data_loader.py
import json
from pathlib import Path
import streamlit as st


DATA_DIR = Path("data")
@st.cache_data
def load_week(week: int,year):
    path = DATA_DIR / f"week_{week}_{year}_tackles.json"
    if not path.exists():
        return "This week has not happened yet!"
    with open(path, "r") as f:
        return json.load(f)
    
@st.cache_data
def load_all_weeks(year: str):
    all_data = []

        
    for week in range(1, 19):
        all_data.extend(load_week(week, year))
    return all_data

@st.cache_data
def load_member_data():
    path = DATA_DIR / "league_members.json"
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)
