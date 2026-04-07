# aggregator.py
from collections import defaultdict
from data_loader import load_all_weeks,load_member_data

def aggregate_season():
    tackle_data = load_all_weeks()
    member_data= load_member_data()
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
        "display_name": "",
        "team_name": "",
        "tackles_for": 0,
        "tackles_against": 0,
        "impact_wins": 0,
        "still_lost": 0,
        "no_effect": 0,
        "benched": 0,
        "bye_week": 0,
        "free_agent": 0,
        "total_points_for": 0,
        "total_points_against": 0,
        "losses": 0,
    })
    for member in member_data:
        owner_stats[member["user_id"]]["display_name"] = member["display_name"]
        owner_stats[member["user_id"]]["team_name"] = member["team_name"]

    for t in tackle_data:
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
        owner_stats[owner_id]["display_name"] = owner["display_name"]
        owner_stats[owner_id]["tackles_for"] += t["count"]
        owner_stats[owner_id][impact_key(impact)] += 1
        owner_stats[owner_id]["total_points_for"]+=t["points"]

        # Tackles against
        owner_stats[opp_id]["tackles_against"] += t["count"]
        owner_stats[opp_id]["team_name"] = opp["team_name"]
        owner_stats[opp_id]["display_name"] = opp["display_name"]
        if impact == "Win":
            owner_stats[opp_id]["losses"] += 1
        owner_stats[opp_id]["total_points_against"] += t["points"]

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
