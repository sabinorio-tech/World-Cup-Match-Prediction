# Player Data Pipeline

## Purpose

This enrichment step supplies free tournament player data to the Teams Dashboard. It complements the existing live-match, prediction, Elo, and Streamlit layers.

## Source Research

### FBref

FBref has strong football analytics coverage when tables are available, including standard, shooting, passing, defensive, possession, and miscellaneous player statistics. However, it is not the best automated source for this project because direct automated access is fragile and can be blocked. It also does not provide player portraits.

### StatBunker

StatBunker has public FIFA World Cup 2026 pages, including player standings, fantasy/player stats, assists, goals, cards, and shots-related tables. The pages are HTML tables and can be fetched with a browser-like request, saved as raw HTML, and transformed into CSV.

StatBunker is the selected source for this proof of concept because it is free, tournament-specific, and currently exposes World Cup 2026 player rows.

### API-Football

API-Football would be technically cleaner, but the free plan does not provide the needed 2026 World Cup data for this project. It remains a good paid option, but not the selected free source.

## Selected Source

Chosen source: **StatBunker**

Raw pages:

```text
https://www.statbunker.com/competitions/PlayerStandings?comp_id=790
https://www.statbunker.com/competitions/FantasyFootballPlayersStats?comp_id=790
https://www.statbunker.com/competitions/PlayersShotsOnGoal?comp_id=790
```

Raw output folder:

```text
data/raw/player_data/
```

Processed outputs:

```text
data/processed/player_profiles.csv
data/processed/player_stats.csv
```

## Available Statistics

The current pipeline can populate:

```text
player_name
team
position
appearances
starts
substitute_appearances
goals
assists
yellow_cards
red_cards
shots
shots_on_target
```

`shots` and `shots_on_target` are populated only if the StatBunker shots table contains data.

## Unavailable Statistics

These fields are included in `player_stats.csv` for future compatibility, but are not reliably available from the selected free source:

```text
minutes_played
passes
pass_accuracy
key_passes
tackles
interceptions
dribbles
duels_won
fouls_won
```

They are intentionally left empty instead of being estimated or fabricated.

## Player Images

StatBunker and FBref are not reliable free sources for reusable player portraits.

Recommended future image enrichment:

```text
Wikidata / Wikimedia Commons
```

This would allow image URLs, authors, licenses, and attribution metadata to be tracked safely. Coverage will be incomplete, but licensing is clearer than scraping copyrighted profile images.

## Assumptions

- StatBunker team names are used as the first normalization layer.
- Existing project team names should be used later to map variants if needed.
- Raw HTML is saved before transformation so parser issues can be debugged without refetching.
- Missing advanced statistics are documented and left blank.

## How To Run

```bash
python -m src.enrichment.fetch_player_data
```

It also runs as stage 8 of the full pipeline:

```bash
python main.py
```

## Pipeline Flow

```text
Download StatBunker HTML
↓
Save raw HTML
↓
Parse first data table from each page
↓
Normalize player names, teams, positions, and numeric columns
↓
Validate non-empty player outputs
↓
Write processed CSV files
```

## Limitations

- StatBunker is an HTML source, not an official API.
- Page layout changes can break parsing.
- Some advanced stats required by the final Teams Dashboard are not available.
- Player images are not included.
- The production pipeline uses cached raw HTML when StatBunker temporarily blocks or rejects a refresh.

## Recommendation

Continue with this free StatBunker-based player-data pipeline for portfolio purposes. For a production-grade dashboard, use a paid API source or add a separate licensed image and advanced-stat enrichment layer.
