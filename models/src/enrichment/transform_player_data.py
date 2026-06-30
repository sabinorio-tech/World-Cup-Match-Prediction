from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup

from src.enrichment.statbunker_client import PROJECT_ROOT, RAW_DIR

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROFILE_COLUMNS = [
    "player_name",
    "team",
    "position",
    "age",
    "nationality",
    "club",
    "photo_url",
]

STATS_COLUMNS = [
    "player_name",
    "team",
    "position",
    "appearances",
    "starts",
    "substitute_appearances",
    "goals",
    "assists",
    "minutes_played",
    "passes",
    "pass_accuracy",
    "key_passes",
    "shots",
    "shots_on_target",
    "tackles",
    "interceptions",
    "dribbles",
    "duels_won",
    "fouls_won",
    "yellow_cards",
    "red_cards",
]

TEAM_NAME_MAP = {
    "Curacao": "Curaçao",
    "Czech Republic": "Czechia",
    "DR Congo (Zaire)": "DR Congo",
    "Korea Republic": "South Korea",
    "South Korea": "South Korea",
    "Turkey": "Türkiye",
    "United States": "USA",
}


def _clean_text(value: Any) -> str:
    return str(value).replace("\xa0", " ").strip()


def _normalize_team_name(value: Any) -> str:
    team = _clean_text(value)
    return TEAM_NAME_MAP.get(team, team)


def _to_number(value: Any) -> Any:
    text = _clean_text(value)
    if text in {"", "-", "nan", "None"}:
        return pd.NA
    text = text.replace(",", "")
    return pd.to_numeric(text, errors="coerce")


def _unique_headers(headers: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    output = []
    for index, header in enumerate(headers):
        name = header or f"unnamed_{index}"
        counts[name] = counts.get(name, 0) + 1
        if counts[name] > 1:
            name = f"{name}_{counts[name]}"
        output.append(name)
    return output


def parse_first_table(html: str) -> pd.DataFrame:
    """Parse the first StatBunker table defensively, including imperfect HTML."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        return pd.DataFrame()

    header_row = table.find("tr")
    if header_row is None:
        return pd.DataFrame()

    headers = _unique_headers([_clean_text(th.get_text(" ", strip=True)) for th in header_row.find_all("th")])
    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [_clean_text(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])]
        if not cells or cells == ["No data found"]:
            continue
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        if len(cells) > len(headers):
            cells = cells[: len(headers)]
        rows.append(cells)

    return pd.DataFrame(rows, columns=headers)


def load_raw_table(filename: str, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    path = raw_dir / filename
    if not path.exists():
        print(f"Missing raw player-data file: {path}")
        return pd.DataFrame()
    return parse_first_table(path.read_text(encoding="utf-8"))


def _standardize_player_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    renamed = df.rename(
        columns={
            "Players": "player_name",
            "Clubs": "team",
            "Position": "position",
            "Total": "appearances",
            "Goals": "goals",
            "A": "assists",
            "Start": "starts",
            "Sub": "substitute_appearances",
            "Yellow": "yellow_cards",
            "Red": "red_cards",
            "Shots on Target": "shots_on_target",
            "Shots off Target": "shots_off_target",
        }
    ).copy()

    keep = [column for column in renamed.columns if column in {
        "player_name",
        "team",
        "position",
        "appearances",
        "goals",
        "assists",
        "starts",
        "substitute_appearances",
        "yellow_cards",
        "red_cards",
        "shots_on_target",
        "shots_off_target",
    }]
    renamed = renamed[keep]
    if "player_name" in renamed.columns:
        renamed["player_name"] = renamed["player_name"].map(_clean_text)
    if "team" in renamed.columns:
        renamed["team"] = renamed["team"].map(_normalize_team_name)
    if "position" in renamed.columns:
        renamed["position"] = renamed["position"].map(_clean_text)

    for column in set(renamed.columns) - {"player_name", "team", "position"}:
        renamed[column] = renamed[column].map(_to_number)
    return renamed


def build_player_profiles(overall: pd.DataFrame) -> pd.DataFrame:
    if overall.empty:
        return pd.DataFrame(columns=PROFILE_COLUMNS)
    profiles = overall[["player_name", "team", "position"]].drop_duplicates().copy()
    profiles["age"] = pd.NA
    profiles["nationality"] = pd.NA
    profiles["club"] = pd.NA
    profiles["photo_url"] = pd.NA
    return profiles[PROFILE_COLUMNS].sort_values(["team", "player_name"]).reset_index(drop=True)


def build_player_stats(overall: pd.DataFrame, fantasy: pd.DataFrame, shots: pd.DataFrame) -> pd.DataFrame:
    if overall.empty:
        return pd.DataFrame(columns=STATS_COLUMNS)

    stats = overall.copy()
    fantasy_cols = [column for column in ["player_name", "yellow_cards", "red_cards"] if column in fantasy.columns]
    if len(fantasy_cols) > 1:
        stats = stats.merge(
            fantasy[fantasy_cols].drop_duplicates("player_name"),
            on="player_name",
            how="left",
            suffixes=("", "_fantasy"),
        )
        for column in ["yellow_cards", "red_cards"]:
            fantasy_column = f"{column}_fantasy"
            if fantasy_column in stats.columns:
                stats[column] = stats.get(column, pd.NA).fillna(stats[fantasy_column])
                stats = stats.drop(columns=[fantasy_column])

    shot_cols = [column for column in ["player_name", "shots_on_target", "shots_off_target"] if column in shots.columns]
    if len(shot_cols) > 1:
        stats = stats.merge(
            shots[shot_cols].drop_duplicates("player_name"),
            on="player_name",
            how="left",
            suffixes=("", "_shots"),
        )

    if "shots" not in stats.columns:
        if {"shots_on_target", "shots_off_target"}.issubset(stats.columns):
            stats["shots"] = stats["shots_on_target"].fillna(0) + stats["shots_off_target"].fillna(0)
        else:
            stats["shots"] = pd.NA

    for column in STATS_COLUMNS:
        if column not in stats.columns:
            stats[column] = pd.NA

    return stats[STATS_COLUMNS].sort_values(["team", "player_name"]).reset_index(drop=True)


def _save_csv(df: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")
    print(f"Rows: {len(df)}")
    return output_path


def validate_outputs(profiles: pd.DataFrame, stats: pd.DataFrame) -> None:
    if profiles.empty:
        raise ValueError("player_profiles.csv would be empty.")
    if stats.empty:
        raise ValueError("player_stats.csv would be empty.")
    if profiles["player_name"].isna().any() or stats["player_name"].isna().any():
        raise ValueError("Player data contains missing player names.")
    if profiles["team"].isna().any() or stats["team"].isna().any():
        raise ValueError("Player data contains missing team names.")


def transform_player_data(raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR) -> list[Path]:
    overall = _standardize_player_table(load_raw_table("statbunker_player_standings.html", raw_dir))
    fantasy = _standardize_player_table(load_raw_table("statbunker_fantasy_players.html", raw_dir))
    shots = _standardize_player_table(load_raw_table("statbunker_shots_on_goal.html", raw_dir))

    profiles = build_player_profiles(overall)
    stats = build_player_stats(overall, fantasy, shots)
    validate_outputs(profiles, stats)

    return [
        _save_csv(profiles, processed_dir / "player_profiles.csv"),
        _save_csv(stats, processed_dir / "player_stats.csv"),
    ]


if __name__ == "__main__":
    transform_player_data()
