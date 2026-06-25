"""
Builds ONE deterministic "most likely path" bracket tree, the way the
mockup's Knockout Bracket page shows a single tree with a percentage at
each node — as opposed to simulate.py's 3,000-run Monte Carlo, which
gives the *distribution* of outcomes (used for the "Chance to win the
tournament" cards alongside this tree).

Methodology (flagged on the About page, same spirit as simulate.py):
  - "Most likely" group occupants = current actual points + each
    remaining match's expected points (win_prob*3 + draw_prob*1),
    ranked. Top 2 per group qualify directly; the 8 highest-scoring
    3rd-place teams across all 12 groups fill the wildcard slots.
  - The real official Round-of-32 skeleton is used for pairings
    (1A vs 2B, etc.); the 8 wildcard teams are seeded into the 4
    "Best 3rd" slots by rank (highest two together, etc.) — a
    simplification, since the official slot-assignment table depends
    on which specific group combination of thirds qualifies.
  - Every match's winner is whichever team has the higher Elo-based
    win probability — a single deterministic pick, not a sample.
"""

from __future__ import annotations

from functools import lru_cache

import realdata as rd


def _elo_win_prob(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(elo_a - elo_b) / 400.0))


@lru_cache(maxsize=1)
def _expected_final_points() -> dict:
    matches = rd.load_group_matches()
    campaign = rd.load_campaign_stats()
    teams = rd.load_teams()["team"].tolist()
    points = {t: float(campaign.get(t, {}).get("points", 0)) for t in teams}

    unplayed = matches[~matches["played"]]
    for _, m in unplayed.iterrows():
        points[m.team1] += m.team1_win_prob * 3 + m.draw_prob * 1
        points[m.team2] += m.team2_win_prob * 3 + m.draw_prob * 1
    return points


@lru_cache(maxsize=1)
def most_likely_qualifiers() -> dict:
    """Returns {'1A': team_name, '2A': team_name, ..., 'Best 3rd #1': team_name, ...}."""
    points = _expected_final_points()
    teams_df = rd.load_teams()
    groups = teams_df.groupby("group")["team"].apply(list).to_dict()

    slots = {}
    thirds = []  # (points, group, team)
    for group, members in groups.items():
        ranked = sorted(members, key=lambda t: -points[t])
        slots[f"1{group}"] = ranked[0]
        slots[f"2{group}"] = ranked[1]
        thirds.append((points[ranked[2]], group, ranked[2]))

    thirds.sort(key=lambda x: -x[0])
    best8 = thirds[:8]
    for i, (_, _, team) in enumerate(best8):
        slots[f"Best 3rd #{i+1}"] = team
    return slots


def build_bracket() -> dict:
    """Returns {'round_of_32': [...], 'round_of_16': [...], 'quarterfinal': [...],
    'semifinal': [...], 'final': [...], 'champion': team_name}, where each
    round's list holds dicts: {team1, team2, prob1, prob2, winner}."""
    slots = most_likely_qualifiers()
    elo = rd.load_teams().set_index("team")["elo"].to_dict()
    ko = rd.load_knockout_skeleton()
    r32_rows = ko[ko["stage"] == "Round of 32"]
    fixed_pairs = [(r.team1, r.team2) for _, r in r32_rows.iterrows() if "Best 3rd" not in r.team1]

    matchups = [(slots[a], slots[b]) for a, b in fixed_pairs]
    # Seed the 8 wildcards: rank 1&2 together, 3&4, 5&6, 7&8.
    wildcards = [slots[f"Best 3rd #{i+1}"] for i in range(8)]
    for i in range(0, 8, 2):
        matchups.append((wildcards[i], wildcards[i + 1]))

    def play_round(pairs):
        results = []
        winners = []
        for a, b in pairs:
            p_a = _elo_win_prob(elo[a], elo[b])
            winner = a if p_a >= 0.5 else b
            results.append({"team1": a, "team2": b, "prob1": round(p_a, 3),
                             "prob2": round(1 - p_a, 3), "winner": winner})
            winners.append(winner)
        return results, winners

    bracket = {}
    bracket["round_of_32"], winners = play_round(matchups)

    next_pairs = [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]
    bracket["round_of_16"], winners = play_round(next_pairs)

    next_pairs = [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]
    bracket["quarterfinal"], winners = play_round(next_pairs)

    next_pairs = [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]
    bracket["semifinal"], winners = play_round(next_pairs)

    next_pairs = [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]
    bracket["final"], winners = play_round(next_pairs)

    bracket["champion"] = winners[0]
    return bracket
