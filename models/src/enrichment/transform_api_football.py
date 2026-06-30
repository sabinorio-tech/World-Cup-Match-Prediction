from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.enrichment.api_football_client import PROJECT_ROOT, RAW_DIR, load_json

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _response(raw: dict[str, Any]) -> list[Any]:
    value = raw.get("response", [])
    return value if isinstance(value, list) else []


def _save_if_not_empty(df: pd.DataFrame, output_path: Path) -> Path | None:
    if df.empty:
        print(f"Skipped empty output: {output_path}")
        return None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")
    print(f"Rows: {len(df)}")
    return output_path


def _read_raw(filename: str, raw_dir: Path = RAW_DIR) -> dict[str, Any]:
    path = raw_dir / filename
    if not path.exists():
        return {}
    return load_json(path)


def transform_teams(raw: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for item in _response(raw):
        team = _as_dict(_as_dict(item).get("team"))
        venue = _as_dict(_as_dict(item).get("venue"))
        rows.append(
            {
                "team_id": team.get("id"),
                "team_name": team.get("name"),
                "team_code": team.get("code"),
                "country": team.get("country"),
                "national": team.get("national"),
                "logo_url": team.get("logo"),
                "venue_id": venue.get("id"),
                "venue_name": venue.get("name"),
                "venue_city": venue.get("city"),
            }
        )
    return pd.DataFrame(rows)


def transform_player_profiles(raw: dict[str, Any], team_id: int | None = None, team_name: str | None = None) -> pd.DataFrame:
    rows = []
    for item in _response(raw):
        team = _as_dict(_as_dict(item).get("team"))
        for player in _as_dict(item).get("players", []) or []:
            player = _as_dict(player)
            rows.append(
                {
                    "player_id": player.get("id"),
                    "player_name": player.get("name"),
                    "team_id": team.get("id", team_id),
                    "team_name": team.get("name", team_name),
                    "age": player.get("age"),
                    "number": player.get("number"),
                    "position": player.get("position"),
                    "photo_url": player.get("photo"),
                }
            )
    return pd.DataFrame(rows)


def transform_player_stats(raw: dict[str, Any], fallback_team_id: int | None = None, fallback_team_name: str | None = None) -> pd.DataFrame:
    rows = []
    for item in _response(raw):
        item = _as_dict(item)
        player = _as_dict(item.get("player"))
        for stat in item.get("statistics", []) or []:
            stat = _as_dict(stat)
            team = _as_dict(stat.get("team"))
            games = _as_dict(stat.get("games"))
            goals = _as_dict(stat.get("goals"))
            passes = _as_dict(stat.get("passes"))
            shots = _as_dict(stat.get("shots"))
            tackles = _as_dict(stat.get("tackles"))
            dribbles = _as_dict(stat.get("dribbles"))
            duels = _as_dict(stat.get("duels"))
            fouls = _as_dict(stat.get("fouls"))
            cards = _as_dict(stat.get("cards"))

            rows.append(
                {
                    "player_id": player.get("id"),
                    "player_name": player.get("name"),
                    "team_id": team.get("id", fallback_team_id),
                    "team_name": team.get("name", fallback_team_name),
                    "position": games.get("position"),
                    "minutes_played": games.get("minutes"),
                    "goals": goals.get("total"),
                    "assists": goals.get("assists"),
                    "passes": passes.get("total"),
                    "pass_accuracy": passes.get("accuracy"),
                    "shots": shots.get("total"),
                    "shots_on_target": shots.get("on"),
                    "chances_created": passes.get("key"),
                    "tackles": tackles.get("total"),
                    "interceptions": tackles.get("interceptions"),
                    "dribbles_attempted": dribbles.get("attempts"),
                    "dribbles_success": dribbles.get("success"),
                    "duels_total": duels.get("total"),
                    "duels_won": duels.get("won"),
                    "fouls_drawn": fouls.get("drawn"),
                    "yellow_cards": cards.get("yellow"),
                    "red_cards": cards.get("red"),
                }
            )
    return pd.DataFrame(rows)


def transform_fixture_events(raw: dict[str, Any]) -> pd.DataFrame:
    fixture_id = _as_dict(raw.get("parameters")).get("fixture")
    rows = []
    for event in _response(raw):
        event = _as_dict(event)
        team = _as_dict(event.get("team"))
        player = _as_dict(event.get("player"))
        assist = _as_dict(event.get("assist"))
        time = _as_dict(event.get("time"))
        rows.append(
            {
                "fixture_id": fixture_id,
                "team_id": team.get("id"),
                "team_name": team.get("name"),
                "player_id": player.get("id"),
                "player_name": player.get("name"),
                "assist_id": assist.get("id"),
                "assist_name": assist.get("name"),
                "event_type": event.get("type"),
                "event_detail": event.get("detail"),
                "elapsed": time.get("elapsed"),
                "extra": time.get("extra"),
                "comments": event.get("comments"),
            }
        )
    return pd.DataFrame(rows)


def transform_fixture_statistics(raw: dict[str, Any]) -> pd.DataFrame:
    fixture_id = _as_dict(raw.get("parameters")).get("fixture")
    rows = []
    for item in _response(raw):
        item = _as_dict(item)
        team = _as_dict(item.get("team"))
        for stat in item.get("statistics", []) or []:
            stat = _as_dict(stat)
            rows.append(
                {
                    "fixture_id": fixture_id,
                    "team_id": team.get("id"),
                    "team_name": team.get("name"),
                    "stat_type": stat.get("type"),
                    "stat_value": stat.get("value"),
                }
            )
    return pd.DataFrame(rows)


def transform_fixture_player_stats(raw: dict[str, Any]) -> pd.DataFrame:
    fixture_id = _as_dict(raw.get("parameters")).get("fixture")
    rows = []
    for team_item in _response(raw):
        team_item = _as_dict(team_item)
        team = _as_dict(team_item.get("team"))
        for player_item in team_item.get("players", []) or []:
            player_item = _as_dict(player_item)
            player = _as_dict(player_item.get("player"))
            for stat in player_item.get("statistics", []) or []:
                stat = _as_dict(stat)
                games = _as_dict(stat.get("games"))
                goals = _as_dict(stat.get("goals"))
                passes = _as_dict(stat.get("passes"))
                shots = _as_dict(stat.get("shots"))
                tackles = _as_dict(stat.get("tackles"))
                dribbles = _as_dict(stat.get("dribbles"))
                duels = _as_dict(stat.get("duels"))
                fouls = _as_dict(stat.get("fouls"))
                cards = _as_dict(stat.get("cards"))
                rows.append(
                    {
                        "fixture_id": fixture_id,
                        "team_id": team.get("id"),
                        "team_name": team.get("name"),
                        "player_id": player.get("id"),
                        "player_name": player.get("name"),
                        "position": games.get("position"),
                        "minutes_played": games.get("minutes"),
                        "goals": goals.get("total"),
                        "assists": goals.get("assists"),
                        "passes": passes.get("total"),
                        "pass_accuracy": passes.get("accuracy"),
                        "shots": shots.get("total"),
                        "shots_on_target": shots.get("on"),
                        "chances_created": passes.get("key"),
                        "tackles": tackles.get("total"),
                        "interceptions": tackles.get("interceptions"),
                        "dribbles_attempted": dribbles.get("attempts"),
                        "dribbles_success": dribbles.get("success"),
                        "duels_total": duels.get("total"),
                        "duels_won": duels.get("won"),
                        "fouls_drawn": fouls.get("drawn"),
                        "yellow_cards": cards.get("yellow"),
                        "red_cards": cards.get("red"),
                    }
                )
    return pd.DataFrame(rows)


def transform_api_football_outputs(raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR) -> list[Path]:
    created: list[Path] = []

    outputs = [
        (transform_teams(_read_raw("wc_2026_teams.json", raw_dir)), processed_dir / "api_football_teams.csv"),
        (transform_player_profiles(_read_raw("selected_team_squad.json", raw_dir)), processed_dir / "api_football_player_profiles.csv"),
        (transform_player_stats(_read_raw("selected_team_player_stats.json", raw_dir)), processed_dir / "api_football_player_stats.csv"),
        (transform_fixture_events(_read_raw("selected_fixture_events.json", raw_dir)), processed_dir / "api_football_fixture_events.csv"),
        (transform_fixture_statistics(_read_raw("selected_fixture_statistics.json", raw_dir)), processed_dir / "api_football_fixture_statistics.csv"),
        (transform_fixture_player_stats(_read_raw("selected_fixture_players.json", raw_dir)), processed_dir / "api_football_fixture_player_stats.csv"),
    ]

    for df, output_path in outputs:
        path = _save_if_not_empty(df, output_path)
        if path is not None:
            created.append(path)

    return created


if __name__ == "__main__":
    transform_api_football_outputs()
