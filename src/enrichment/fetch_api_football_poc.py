from __future__ import annotations

from pathlib import Path
from typing import Any

from src.enrichment.api_football_client import ApiFootballClient, PROJECT_ROOT, RAW_DIR, save_json
from src.enrichment.transform_api_football import PROCESSED_DIR, transform_api_football_outputs

LEAGUE_ID = 1
SEASON = 2026
REPORT_PATH = PROJECT_ROOT / "docs" / "api_football_poc_report.md"

REQUESTS = [
    ("leagues", {"id": LEAGUE_ID, "season": SEASON}, "wc_2026_league.json"),
    ("fixtures", {"league": LEAGUE_ID, "season": SEASON}, "wc_2026_fixtures.json"),
    ("teams", {"league": LEAGUE_ID, "season": SEASON}, "wc_2026_teams.json"),
    ("standings", {"league": LEAGUE_ID, "season": SEASON}, "wc_2026_standings.json"),
]


def _response(raw: dict[str, Any]) -> list[Any]:
    value = raw.get("response", [])
    return value if isinstance(value, list) else []


def _result_count(raw: dict[str, Any]) -> int:
    result = raw.get("results")
    if isinstance(result, int):
        return result
    return len(_response(raw))


def _errors(raw: dict[str, Any]) -> Any:
    errors = raw.get("errors", {})
    return errors if errors else ""


def _select_team(teams_raw: dict[str, Any]) -> tuple[int | None, str | None]:
    for item in _response(teams_raw):
        team = item.get("team", {}) if isinstance(item, dict) else {}
        team_id = team.get("id")
        if team_id is not None:
            return int(team_id), team.get("name")
    return None, None


def _select_fixture(fixtures_raw: dict[str, Any]) -> tuple[int | None, str]:
    fixtures = [item for item in _response(fixtures_raw) if isinstance(item, dict)]
    if not fixtures:
        return None, "none"

    finished = [
        item for item in fixtures
        if item.get("fixture", {}).get("status", {}).get("short") in {"FT", "AET", "PEN"}
        or item.get("fixture", {}).get("status", {}).get("long") == "Match Finished"
    ]
    selected = finished[0] if finished else fixtures[0]
    fixture_id = selected.get("fixture", {}).get("id")
    reason = "finished fixture" if finished else "first available fixture"
    return int(fixture_id) if fixture_id is not None else None, reason


def _save_endpoint(
    client: ApiFootballClient,
    endpoint: str,
    params: dict[str, Any],
    filename: str,
    summary: list[dict[str, Any]],
) -> dict[str, Any]:
    print(f"Fetching /{endpoint} -> {filename}")
    raw = client.get(endpoint, params=params)
    save_json(raw, filename)
    summary.append(
        {
            "endpoint": f"/{endpoint}",
            "params": params,
            "filename": filename,
            "results": _result_count(raw),
            "errors": _errors(raw),
        }
    )
    return raw


def _write_report(
    endpoint_summary: list[dict[str, Any]],
    created_files: list[Path],
    selected_team_id: int | None,
    selected_team_name: str | None,
    selected_fixture_id: int | None,
    fixture_selection_reason: str,
) -> Path:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw_files = sorted(path.name for path in RAW_DIR.glob("*.json"))
    processed_names = [path.name for path in created_files]

    endpoint_rows = "\n".join(
        f"| `{item['endpoint']}` | `{item['params']}` | `{item['filename']}` | {item['results']} | `{item['errors']}` |"
        for item in endpoint_summary
    )
    processed_rows = "\n".join(f"- `data/processed/{name}`" for name in processed_names) or "- No processed CSVs were created."
    raw_rows = "\n".join(f"- `data/raw/api_football/{name}`" for name in raw_files) or "- No raw files were created."

    report = f"""# API-Football Proof of Concept Report

## Purpose

This proof of concept tests whether API-Football can enrich the Teams page with squads, player profiles, player statistics, match events, match statistics, and player-level fixture statistics.

## Configuration

- League: `{LEAGUE_ID}` FIFA World Cup
- Season: `{SEASON}`
- Selected team: `{selected_team_name or 'not available'}` (`{selected_team_id or 'n/a'}`)
- Selected fixture: `{selected_fixture_id or 'not available'}`
- Fixture selection: `{fixture_selection_reason}`
- API key source: `API_FOOTBALL_KEY`

## Endpoints Tested

| Endpoint | Params | Raw file | Results | Errors |
|---|---|---:|---:|---|
{endpoint_rows}

## Raw Files Saved

{raw_rows}

## Processed Files Created

{processed_rows}

## Dashboard Field Coverage

| Dashboard need | POC source | Status |
|---|---|---|
| Teams | `/teams` | Available if response has rows |
| Team logos | `/teams` | Available as `team.logo` |
| Player profiles | `/players/squads` | Available if squad endpoint has rows |
| Player images | `/players/squads`, `/players` | Available as player `photo` when populated |
| Player season statistics | `/players` | Available if competition coverage exposes player stats |
| Match events | `/fixtures/events` | Available after fixture data exists |
| Team match statistics | `/fixtures/statistics` | Available after fixture data exists |
| Fixture player statistics | `/fixtures/players` | Available after fixture data exists and coverage supports it |
| Lineups/formations | `/fixtures/lineups` | Raw response saved for inspection |

## Notes

- Empty API responses are saved as raw JSON and skipped during CSV transformation.
- If no finished fixture is available, match-level events/statistics/player stats may be empty until matches are played.
- This POC is intentionally not wired into `main.py` or the Streamlit dashboard.

## Approximate Request Count

This run makes up to `10` API requests:

1. League coverage
2. Fixtures
3. Teams
4. Standings
5. Selected team squad
6. Selected team player statistics
7. Selected fixture events
8. Selected fixture statistics
9. Selected fixture player stats
10. Selected fixture lineups

## Recommendation

Partial continue. Use this POC output to verify actual World Cup 2026 coverage with your API key before replacing any existing source.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Saved: {REPORT_PATH}")
    return REPORT_PATH


def run_api_football_poc() -> None:
    client = ApiFootballClient()
    endpoint_summary: list[dict[str, Any]] = []

    raw_by_file: dict[str, dict[str, Any]] = {}
    for endpoint, params, filename in REQUESTS:
        raw_by_file[filename] = _save_endpoint(client, endpoint, params, filename, endpoint_summary)

    selected_team_id, selected_team_name = _select_team(raw_by_file["wc_2026_teams.json"])
    if selected_team_id is not None:
        _save_endpoint(
            client,
            "players/squads",
            {"team": selected_team_id},
            "selected_team_squad.json",
            endpoint_summary,
        )
        _save_endpoint(
            client,
            "players",
            {"league": LEAGUE_ID, "season": SEASON, "team": selected_team_id},
            "selected_team_player_stats.json",
            endpoint_summary,
        )
    else:
        print("No team found in /teams response. Skipping team-specific endpoints.")

    selected_fixture_id, fixture_selection_reason = _select_fixture(raw_by_file["wc_2026_fixtures.json"])
    if selected_fixture_id is not None:
        fixture_requests = [
            ("fixtures/events", {"fixture": selected_fixture_id}, "selected_fixture_events.json"),
            ("fixtures/statistics", {"fixture": selected_fixture_id}, "selected_fixture_statistics.json"),
            ("fixtures/players", {"fixture": selected_fixture_id}, "selected_fixture_players.json"),
            ("fixtures/lineups", {"fixture": selected_fixture_id}, "selected_fixture_lineups.json"),
        ]
        for endpoint, params, filename in fixture_requests:
            _save_endpoint(client, endpoint, params, filename, endpoint_summary)
    else:
        print("No fixture found in /fixtures response. Skipping fixture-specific endpoints.")

    created_files = transform_api_football_outputs()
    _write_report(
        endpoint_summary=endpoint_summary,
        created_files=created_files,
        selected_team_id=selected_team_id,
        selected_team_name=selected_team_name,
        selected_fixture_id=selected_fixture_id,
        fixture_selection_reason=fixture_selection_reason,
    )
    print("API-Football proof of concept completed.")


if __name__ == "__main__":
    try:
        run_api_football_poc()
    except ValueError as exc:
        print(f"API-Football POC stopped: {exc}")
        raise SystemExit(1) from exc
