"""
Monte Carlo simulator for group qualification + knockout progression.

Methodology (kept deliberately transparent, see About page):
  - Group stage: matches already played are FIXED (use the real score).
    Remaining matches are resampled each run from the XGBoost model's own
    win/draw/loss probabilities (predictions_2026.csv) — nothing here
    overrides what the model said.
  - Standings: points only; ties broken by a small random jitter per run
    (a simplification — the real rules use goal difference, head-to-head,
    then disciplinary points, which the model's output doesn't carry).
  - Qualification: top 2 per group (24 teams) + best 8 third-placed teams
    across all 12 groups, exactly matching the official 48-team format.
  - Knockout bracket: uses the REAL official placeholder structure pulled
    from wc_2026_fixtures_enriched.csv (1A vs 2B, etc., through to the
    Final). The four "Best 3rd" R32 slots are filled by randomly pairing
    the 8 qualifying third-place teams each run, since their exact slot
    assignment depends on which group combination qualifies (an official
    lookup table this dataset doesn't include).
  - Knockout win probability: since the trained classifier needs full
    per-match features we don't have for hypothetical knockout pairings,
    knockout matches use the standard Elo logistic win curve on
    elo_latest.csv ratings. This is a clearly-flagged approximation layered
    on top of the model's own group-stage predictions, not a replacement
    for them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import realdata as rd
from cache_utils import ttl_cache

N_SIMS = 3000
RNG_SEED = 2026


def _elo_win_prob(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(elo_a - elo_b) / 400.0))


@ttl_cache()
def _team_index():
    teams = rd.load_teams()
    names = teams["team"].tolist()
    return {name: i for i, name in enumerate(names)}, names, teams.set_index("team")["elo"].to_dict()


@ttl_cache()
def run_simulation(n_sims: int = N_SIMS, seed: int = RNG_SEED):
    rng = np.random.default_rng(seed)
    idx_of, names, elo_of = _team_index()
    n_teams = len(names)

    matches = rd.load_group_matches()
    campaign = rd.load_campaign_stats()

    # Points already locked in from real results.
    base_points = np.zeros(n_teams)
    for team, s in campaign.items():
        base_points[idx_of[team]] = s["points"]

    points = np.tile(base_points, (n_sims, 1))  # (n_sims, n_teams)

    unplayed = matches[~matches["played"]]
    for _, m in unplayed.iterrows():
        i1, i2 = idx_of[m.team1], idx_of[m.team2]
        probs = [m.team1_win_prob, m.draw_prob, m.team2_win_prob]
        probs = np.array(probs) / sum(probs)
        outcomes = rng.choice(3, size=n_sims, p=probs)  # 0=team1 win, 1=draw, 2=team2 win
        points[outcomes == 0, i1] += 3
        points[outcomes == 1, i1] += 1
        points[outcomes == 1, i2] += 1
        points[outcomes == 2, i2] += 3

    jitter = rng.random((n_sims, n_teams)) * 1e-3  # break ties without favoring anyone
    ranked_points = points + jitter

    groups = rd.load_teams().groupby("group")["team"].apply(list).to_dict()

    qualified = np.zeros((n_sims, n_teams), dtype=bool)
    group_rank = np.zeros((n_sims, n_teams), dtype=int)  # 1/2/3/4 within group
    third_place_points = {}  # group -> (n_sims,) points of the 3rd-ranked team
    third_place_team_idx = {}  # group -> (n_sims,) team index of the 3rd-ranked team

    for group, members in groups.items():
        member_idx = [idx_of[t] for t in members]
        sub = ranked_points[:, member_idx]  # (n_sims, 4)
        order = np.argsort(-sub, axis=1)  # best -> worst, per sim
        ranked_member_idx = np.array(member_idx)[order]  # (n_sims, 4) actual team indices, ranked

        for rank in range(4):
            cols = ranked_member_idx[:, rank]
            group_rank[np.arange(n_sims), cols] = rank + 1
            if rank < 2:
                qualified[np.arange(n_sims), cols] = True

        third_place_team_idx[group] = ranked_member_idx[:, 2]
        third_place_points[group] = points[np.arange(n_sims), ranked_member_idx[:, 2]]

    # Rank the 12 third-placed teams per sim, take top 8.
    group_order = sorted(groups.keys())
    third_points_matrix = np.stack([third_place_points[g] for g in group_order], axis=1)  # (n_sims, 12)
    third_idx_matrix = np.stack([third_place_team_idx[g] for g in group_order], axis=1)   # (n_sims, 12)
    third_jitter = rng.random(third_points_matrix.shape) * 1e-3
    third_order = np.argsort(-(third_points_matrix + third_jitter), axis=1)  # best -> worst
    best8_team_idx = np.take_along_axis(third_idx_matrix, third_order[:, :8], axis=1)  # (n_sims, 8)
    for col in range(8):
        qualified[np.arange(n_sims), best8_team_idx[:, col]] = True

    # ---- Knockout bracket, using the real official R32 pairing skeleton ----
    ko = rd.load_knockout_skeleton()
    r32_rows = ko[ko["stage"] == "Round of 32"]
    fixed_pairs = [(r.team1, r.team2) for _, r in r32_rows.iterrows() if "Best 3rd" not in r.team1]

    reach = {round_name: np.zeros(n_teams, dtype=int)
             for round_name in ["round_of_32", "round_of_16", "quarterfinal", "semifinal", "final", "winner"]}

    elo_arr = np.array([elo_of[n] for n in names])

    for sim in range(n_sims):
        # Resolve 1X/2X labels to actual team indices for this sim.
        slot_team = {}
        for group in group_order:
            member_idx = [idx_of[t] for t in groups[group]]
            ranks_here = group_rank[sim, member_idx]
            for local_i, team_idx in zip(ranks_here, member_idx):
                if local_i == 1:
                    slot_team[f"1{group}"] = team_idx
                elif local_i == 2:
                    slot_team[f"2{group}"] = team_idx

        r32_entrants = []
        r32_matchups = []
        for a, b in fixed_pairs:
            r32_matchups.append((slot_team[a], slot_team[b]))

        thirds_this_sim = list(best8_team_idx[sim])
        rng.shuffle(thirds_this_sim)
        for i in range(0, 8, 2):
            r32_matchups.append((thirds_this_sim[i], thirds_this_sim[i + 1]))

        for a, b in r32_matchups:
            reach["round_of_32"][a] += 1
            reach["round_of_32"][b] += 1

        round_winners = r32_matchups
        # Each label is the round the *winners* of this round of matches reach.
        round_names = ["round_of_16", "quarterfinal", "semifinal", "final"]
        for round_name in round_names:
            next_round = []
            winners_this_round = []
            for a, b in round_winners:
                p_a = _elo_win_prob(elo_arr[a], elo_arr[b])
                winner = a if rng.random() < p_a else b
                winners_this_round.append(winner)
            for w in winners_this_round:
                reach[round_name][w] += 1
            for i in range(0, len(winners_this_round), 2):
                next_round.append((winners_this_round[i], winners_this_round[i + 1]))
            round_winners = next_round

        # round_winners is now [(finalist_a, finalist_b)] — play the Final itself.
        finalist_a, finalist_b = round_winners[0]
        p_a = _elo_win_prob(elo_arr[finalist_a], elo_arr[finalist_b])
        champion = finalist_a if rng.random() < p_a else finalist_b
        reach["winner"][champion] += 1

    rows = []
    for i, name in enumerate(names):
        rows.append({
            "team": name,
            "group_qualification_probability": qualified[:, i].mean(),
            "round_of_32": reach["round_of_32"][i] / n_sims,
            "round_of_16": reach["round_of_16"][i] / n_sims,
            "quarterfinal": reach["quarterfinal"][i] / n_sims,
            "semifinal": reach["semifinal"][i] / n_sims,
            "final": reach["final"][i] / n_sims,
            "tournament_win_probability": reach["winner"][i] / n_sims,
        })
    df = pd.DataFrame(rows).sort_values("tournament_win_probability", ascending=False).reset_index(drop=True)
    return df
