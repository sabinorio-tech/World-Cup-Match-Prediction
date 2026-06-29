# API-Football Proof of Concept Report

## Purpose

This proof of concept tests whether API-Football can enrich the Teams page with squads, player profiles, player statistics, match events, match statistics, and player-level fixture statistics.

## Configuration

- League: `1` FIFA World Cup
- Season: `2026`
- Selected team: `not available` (`n/a`)
- Selected fixture: `not available`
- Fixture selection: `none`
- API key source: `API_FOOTBALL_KEY`

## Endpoints Tested

| Endpoint | Params | Raw file | Results | Errors |
|---|---|---:|---:|---|
| `/leagues` | `{'id': 1, 'season': 2026}` | `wc_2026_league.json` | 0 | `{'plan': 'Free plans do not have access to this season, try from 2022 to 2024.'}` |
| `/fixtures` | `{'league': 1, 'season': 2026}` | `wc_2026_fixtures.json` | 0 | `{'plan': 'Free plans do not have access to this season, try from 2022 to 2024.'}` |
| `/teams` | `{'league': 1, 'season': 2026}` | `wc_2026_teams.json` | 0 | `{'plan': 'Free plans do not have access to this season, try from 2022 to 2024.'}` |
| `/standings` | `{'league': 1, 'season': 2026}` | `wc_2026_standings.json` | 0 | `{'plan': 'Free plans do not have access to this season, try from 2022 to 2024.'}` |

## Raw Files Saved

- `data/raw/api_football/wc_2026_fixtures.json`
- `data/raw/api_football/wc_2026_league.json`
- `data/raw/api_football/wc_2026_standings.json`
- `data/raw/api_football/wc_2026_teams.json`

## Processed Files Created

- No processed CSVs were created.

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

**No Go as the project's free production source.** The free plan does not expose the required 2026 season. The implementation is retained as a documented POC, while football-data.org provides live fixtures/results and StatBunker provides the current free player enrichment.
