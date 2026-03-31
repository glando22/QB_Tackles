# aggregator.py
from collections import defaultdict
from data_loader import load_all_weeks

def aggregate_season():
    data = load_all_weeks()

    qb_stats = defaultdict(lambda: {
        "name": "",
        "team": "",
        "tackles": 0,
        "impact_wins": 0,
        "still_lost": 0,
        "no_effect": 0,
        "benched": 0,
        "bye_week": 0,
        "free_agent": 0,
    })

    owner_stats = defaultdict(lambda: {
        "team_name": "",
        "tackles_for": 0,
        "tackles_against": 0,
        "impact_wins": 0,
        "still_lost": 0,
        "no_effect": 0,
        "benched": 0,
        "bye_week": 0,
        "free_agent": 0,
    })

    for t in data:
        qb = t["qb"]
        owner = t["owner"]
        opp = t["opponent"]

        qb_id = qb["espn_id"]
        owner_id = owner["user_id"]
        opp_id = opp["user_id"]

        impact = t["impact"]

        # QB stats
        qb_stats[qb_id]["name"] = qb["name"]
        qb_stats[qb_id]["team"] = qb["nfl_team"]
        qb_stats[qb_id]["tackles"] += t["count"]
        qb_stats[qb_id][impact_key(impact)] += 1

        # Owner stats
        owner_stats[owner_id]["team_name"] = owner["team_name"]
        owner_stats[owner_id]["tackles_for"] += t["count"]
        owner_stats[owner_id][impact_key(impact)] += 1

        # Tackles against
        owner_stats[opp_id]["tackles_against"] += t["count"]

    return qb_stats, owner_stats


def impact_key(impact: str):
    mapping = {
        "Win": "impact_wins",
        "LMAOOO STILL LOST": "still_lost",
        "No affect": "no_effect",
        "Benched": "benched",
        "Bye Week": "bye_week",
        "Free Agent": "free_agent",
        "NONE": "no_effect",
    }
    return mapping.get(impact, "no_effect")