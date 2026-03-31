# data_loader.py
import json
from pathlib import Path

DATA_DIR = Path("data")

def load_week(week: int):
    path = DATA_DIR / f"week_{week}_tackles.json"
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)

def load_all_weeks():
    all_data = []
    for week in range(1, 19):
        all_data.extend(load_week(week))
    return all_data