from __future__ import annotations

from pathlib import Path
import re
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.match_results import get_match_source_of_truth

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LIVE_MATCHES_PATH = PROCESSED_DIR / "live_matches.csv"
FIXTURES_PATH = PROCESSED_DIR / "wc_2026_fixtures_enriched.csv"
OUTPUT_PATH = PROCESSED_DIR / "knockout_matches.csv"

OUTPUT_COLUMNS = [
    "match_number",
    "match_id",
    "stage",
    "date",
    "kickoff_time",
    "venue",
    "city",
    "country",
    "home_slot",
    "away_slot",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "home_score_penalties",
    "away_score_penalties",
    "status",
    "score_display",
    "winner",
    "result_source",
    "is_resolved",
    "resolution_source",
]

STAGE_LABELS = {
    "LAST_32": "Round of 32",
    "LAST_16": "Round of 16",
    "QUARTER_FINALS": "Quarter-final",
    "SEMI_FINALS": "Semi-final",
    "THIRD_PLACE": "3rd Place Match",
    "FINAL": "Final",
}

OFFICIAL_KNOCKOUT_SLOT_MAP = [
    (73, "LAST_32", "2A", "2B"),
    (74, "LAST_32", "1E", "3A/B/C/D/F"),
    (75, "LAST_32", "1F", "2C"),
    (76, "LAST_32", "1C", "2F"),
    (77, "LAST_32", "1I", "3C/D/F/G/H"),
    (78, "LAST_32", "2E", "2I"),
    (79, "LAST_32", "1A", "3C/E/F/H/I"),
    (80, "LAST_32", "1L", "3E/H/I/J/K"),
    (81, "LAST_32", "1D", "3B/E/F/I/J"),
    (82, "LAST_32", "1G", "3A/E/H/I/J"),
    (83, "LAST_32", "2K", "2L"),
    (84, "LAST_32", "1H", "2J"),
    (85, "LAST_32", "1B", "3E/F/G/I/J"),
    (86, "LAST_32", "1J", "2H"),
    (87, "LAST_32", "1K", "3D/E/I/J/L"),
    (88, "LAST_32", "2D", "2G"),
    (89, "LAST_16", "W73", "W75"),
    (90, "LAST_16", "W74", "W77"),
    (91, "LAST_16", "W76", "W78"),
    (92, "LAST_16", "W79", "W80"),
    (93, "LAST_16", "W83", "W84"),
    (94, "LAST_16", "W81", "W82"),
    (95, "LAST_16", "W86", "W88"),
    (96, "LAST_16", "W85", "W87"),
    (97, "QUARTER_FINALS", "W89", "W90"),
    (98, "QUARTER_FINALS", "W93", "W94"),
    (99, "QUARTER_FINALS", "W91", "W92"),
    (100, "QUARTER_FINALS", "W95", "W96"),
    (101, "SEMI_FINALS", "W97", "W98"),
    (102, "SEMI_FINALS", "W99", "W100"),
    (103, "THIRD_PLACE", "L101", "L102"),
    (104, "FINAL", "W101", "W102"),
]

_SIMPLE_SLOT_RE = re.compile(r"^([12])([A-L])$")

TEAM_NAME_ALIASES = {
    "United States": "USA",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
    "Turkey": "Türkiye",
}


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    return pd.read_csv(path)


def _group_letter(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.startswith("GROUP_"):
        return text.replace("GROUP_", "", 1)
    if len(text) == 1 and text.isalpha():
        return text.upper()
    return text[-1:].upper() if text else None


def _safe_int(value: object) -> int | None:
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return None
    return int(number)


def compute_group_standings(live_matches: pd.DataFrame) -> pd.DataFrame:
    """Compute current group standings from completed group-stage live matches."""
    if live_matches.empty:
        return pd.DataFrame()

    matches = live_matches[
        live_matches["stage"].eq("GROUP_STAGE")
        & live_matches["status"].eq("FINISHED")
        & live_matches["home_team"].notna()
        & live_matches["away_team"].notna()
    ].copy()
    if matches.empty:
        return pd.DataFrame()

    score_cols = ["home_score", "away_score"]
    for col in score_cols:
        matches[col] = pd.to_numeric(matches[col], errors="coerce")
    matches = matches[matches[score_cols].notna().all(axis=1)]

    records: dict[tuple[str, str], dict[str, object]] = {}

    def ensure(group: str, team: str) -> dict[str, object]:
        key = (group, team)
        if key not in records:
            records[key] = {
                "group": group,
                "team": team,
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goal_difference": 0,
                "points": 0,
            }
        return records[key]

    for row in matches.itertuples(index=False):
        group = _group_letter(row.group)
        if not group:
            continue
        home_goals = _safe_int(row.home_score)
        away_goals = _safe_int(row.away_score)
        if home_goals is None or away_goals is None:
            continue

        home = ensure(group, row.home_team)
        away = ensure(group, row.away_team)
        home["played"] += 1
        away["played"] += 1
        home["goals_for"] += home_goals
        home["goals_against"] += away_goals
        away["goals_for"] += away_goals
        away["goals_against"] += home_goals

        if home_goals > away_goals:
            home["wins"] += 1
            away["losses"] += 1
            home["points"] += 3
        elif home_goals < away_goals:
            away["wins"] += 1
            home["losses"] += 1
            away["points"] += 3
        else:
            home["draws"] += 1
            away["draws"] += 1
            home["points"] += 1
            away["points"] += 1

    standings = pd.DataFrame(records.values())
    if standings.empty:
        return standings

    standings["goal_difference"] = standings["goals_for"] - standings["goals_against"]
    return standings.sort_values(
        ["group", "points", "goal_difference", "goals_for", "team"],
        ascending=[True, False, False, False, True],
    ).reset_index(drop=True)


def build_slot_lookup(standings: pd.DataFrame) -> dict[str, str]:
    """Resolve 1A/2A style slots only for groups that have completed all games."""
    if standings.empty:
        return {}

    slots: dict[str, str] = {}
    for group, rows in standings.groupby("group"):
        ranked = rows.sort_values(
            ["points", "goal_difference", "goals_for", "team"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
        group_is_complete = len(ranked) == 4 and ranked["played"].min() >= 3
        if not group_is_complete:
            continue
        if len(ranked) >= 1:
            slots[f"1{group}"] = ranked.iloc[0]["team"]
        if len(ranked) >= 2:
            slots[f"2{group}"] = ranked.iloc[1]["team"]
    return slots


def build_team_slot_lookup(standings: pd.DataFrame) -> dict[str, str]:
    """Map confirmed group finishers back to concrete 1A/2A/3A slots."""
    slots: dict[str, str] = {}
    if standings.empty:
        return slots

    for group, rows in standings.groupby("group"):
        ranked = rows.sort_values(
            ["points", "goal_difference", "goals_for", "team"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
        if len(ranked) != 4 or ranked["played"].min() < 3:
            continue
        for position in range(min(3, len(ranked))):
            slots[str(ranked.iloc[position]["team"])] = f"{position + 1}{group}"
    return slots


def _project_team_name(value: object) -> str | None:
    if pd.isna(value):
        return None
    team = str(value).strip()
    return TEAM_NAME_ALIASES.get(team, team) if team else None


def _resolve_slot(slot: str, slot_lookup: dict[str, str]) -> tuple[str | None, str]:
    slot = str(slot)
    if _SIMPLE_SLOT_RE.match(slot):
        team = slot_lookup.get(slot)
        if team:
            return team, "computed_group_standings"
        return None, "unresolved_incomplete_group"
    if slot.startswith("3"):
        return None, "unresolved_third_place_rule"
    return None, "unresolved_future_round"


def _slot_accepts(expected: str, actual: str | None) -> bool:
    if not actual:
        return False
    if expected == actual:
        return True
    if expected.startswith("3") and actual.startswith("3"):
        return actual[1:] in expected[1:].split("/")
    return False


def _select_live_row(
    candidates: list[dict[str, object]],
    used_ids: set[object],
    home_slot: str,
    away_slot: str,
    team_slot_lookup: dict[str, str],
    expected_home: str | None = None,
    expected_away: str | None = None,
) -> dict[str, object]:
    available = [row for row in candidates if row.get("match_id") not in used_ids]
    for row in available:
        live_home = str(row.get("home_team") or "")
        live_away = str(row.get("away_team") or "")
        if expected_home and expected_away:
            if _project_team_name(live_home) == expected_home and _project_team_name(live_away) == expected_away:
                return row
        elif _slot_accepts(home_slot, team_slot_lookup.get(live_home)) and _slot_accepts(
            away_slot, team_slot_lookup.get(live_away)
        ):
            return row
    return available[0] if available else {}


def _progression_team(
    slot: str,
    slot_lookup: dict[str, str],
    winners: dict[int, str],
    losers: dict[int, str],
) -> str | None:
    if slot.startswith("W") and slot[1:].isdigit():
        return winners.get(int(slot[1:]))
    if slot.startswith("L") and slot[1:].isdigit():
        return losers.get(int(slot[1:]))
    return slot_lookup.get(slot)


def _ordered_live_knockout_rows(live_matches: pd.DataFrame) -> list[dict[str, object]]:
    knockout = live_matches[live_matches["stage"].isin(STAGE_LABELS)].copy()
    if knockout.empty:
        return []
    knockout["utc_date"] = pd.to_datetime(knockout["utc_date"], errors="coerce")
    knockout = knockout.sort_values(["utc_date", "match_id"], na_position="last")
    return knockout.to_dict("records")


def _ordered_fixture_metadata(fixtures: pd.DataFrame) -> list[dict[str, object]]:
    placeholders = fixtures[fixtures["is_placeholder_match"] == True].copy()  # noqa: E712
    if placeholders.empty:
        return []
    placeholders = placeholders.reset_index(drop=True)
    return placeholders.to_dict("records")


def resolve_knockout_matches(
    live_matches_path: Path = LIVE_MATCHES_PATH,
    fixtures_path: Path = FIXTURES_PATH,
) -> pd.DataFrame:
    live_matches = _load_csv(live_matches_path)
    fixtures = _load_csv(fixtures_path)
    standings = compute_group_standings(live_matches)
    slot_lookup = build_slot_lookup(standings)
    team_slot_lookup = build_team_slot_lookup(standings)
    live_rows = _ordered_live_knockout_rows(live_matches)
    live_by_stage = {
        stage: [row for row in live_rows if row.get("stage") == stage]
        for stage in STAGE_LABELS
    }
    fixture_rows = _ordered_fixture_metadata(fixtures)

    rows = []
    used_live_ids: set[object] = set()
    actual_winners: dict[int, str] = {}
    actual_losers: dict[int, str] = {}
    for index, (match_number, stage_api, home_slot, away_slot) in enumerate(OFFICIAL_KNOCKOUT_SLOT_MAP):
        expected_home = _progression_team(home_slot, slot_lookup, actual_winners, actual_losers)
        expected_away = _progression_team(away_slot, slot_lookup, actual_winners, actual_losers)
        live = _select_live_row(
            live_by_stage.get(stage_api, []),
            used_live_ids,
            home_slot,
            away_slot,
            team_slot_lookup,
            expected_home=_project_team_name(expected_home),
            expected_away=_project_team_name(expected_away),
        )
        if live.get("match_id") is not None:
            used_live_ids.add(live["match_id"])
        fixture = fixture_rows[index] if index < len(fixture_rows) else {}

        live_home_team = live.get("home_team")
        live_away_team = live.get("away_team")
        has_confirmed_live_teams = (
            pd.notna(live_home_team)
            and pd.notna(live_away_team)
        )

        if has_confirmed_live_teams:
            # Concrete group slots add useful detail in the Round of 32. Later
            # rounds must retain W/L slots so bracket lineage remains stable.
            if stage_api == "LAST_32":
                home_slot = team_slot_lookup.get(str(live_home_team), home_slot)
                away_slot = team_slot_lookup.get(str(live_away_team), away_slot)
            home_team = _project_team_name(live_home_team)
            away_team = _project_team_name(live_away_team)
            is_resolved = True
            resolution_source = "football_data_api_confirmed"
        else:
            home_team, home_source = _resolve_slot(home_slot, slot_lookup)
            away_team, away_source = _resolve_slot(away_slot, slot_lookup)
            home_team = _project_team_name(home_team)
            away_team = _project_team_name(away_team)
            is_resolved = home_team is not None and away_team is not None

            sources = sorted({home_source, away_source})
            if is_resolved:
                resolution_source = "official_slot_map+computed_group_standings"
            else:
                resolution_source = "+".join(sources)

        truth = get_match_source_of_truth(live, is_knockout=True)
        actual_winner = _project_team_name(truth["winner"])
        if truth["result_source"] == "actual" and actual_winner:
            actual_winners[match_number] = actual_winner
            participants = {home_team, away_team}
            loser = next((team for team in participants if team and team != actual_winner), None)
            if loser:
                actual_losers[match_number] = loser

        rows.append({
            "match_number": match_number,
            "match_id": live.get("match_id", match_number),
            "stage": STAGE_LABELS.get(stage_api, stage_api),
            "date": live.get("match_date") or fixture.get("date"),
            "kickoff_time": live.get("kickoff_time_utc") or fixture.get("kickoff_et"),
            "venue": fixture.get("venue"),
            "city": fixture.get("city"),
            "country": fixture.get("country"),
            "home_slot": home_slot,
            "away_slot": away_slot,
            "home_team": home_team,
            "away_team": away_team,
            "home_goals": live.get("home_score"),
            "away_goals": live.get("away_score"),
            "home_score_penalties": live.get("home_score_penalties"),
            "away_score_penalties": live.get("away_score_penalties"),
            "status": live.get("status", "SCHEDULED"),
            "score_display": live.get("score_display", "TBD"),
            "winner": actual_winner,
            "result_source": truth["result_source"],
            "is_resolved": is_resolved,
            "resolution_source": resolution_source,
        })

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def save_knockout_matches(df: pd.DataFrame, output_path: Path = OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(".tmp")
    df.to_csv(temp_path, index=False)
    temp_path.replace(output_path)
    print(f"Saved: {output_path}")
    print(f"Rows: {len(df)}")
    return output_path


def build_knockout_matches(
    live_matches_path: Path = LIVE_MATCHES_PATH,
    fixtures_path: Path = FIXTURES_PATH,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    knockout_matches = resolve_knockout_matches(live_matches_path, fixtures_path)
    return save_knockout_matches(knockout_matches, output_path)


if __name__ == "__main__":
    try:
        build_knockout_matches()
    except Exception as exc:
        print(f"Knockout fixture resolution failed: {exc}")
        raise SystemExit(1) from exc
