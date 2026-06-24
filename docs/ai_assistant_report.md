# World Cup Assistant

## Document Role

This document is the feature reference for the World Cup Assistant. It explains what the assistant does, which tools it exposes, which data sources it uses, and how the current architecture is organized.

For the build history, implementation milestones, local LLM experiments, and learning journal, see [`ai_assistant_progress_report.md`](ai_assistant_progress_report.md).

## Purpose

The World Cup Assistant is a lightweight natural language interface for the FIFA World Cup 2026 Match Prediction project. Its goal is to let users ask simple football analytics questions without directly opening CSV files, writing pandas queries, or manually calling prediction functions.

The assistant allows users to query project data using natural language-style prompts such as "What is Belgium's Elo rating?", "Show fixtures for Brazil", or "Predict France vs Germany". It routes each question to a specific tool, retrieves the required project data, formats the result, and returns a readable answer.

The feature sits on top of the existing Data Engineering and Data Science layers:

- The Data Engineering layer prepares cleaned and enriched datasets such as Elo ratings, team metadata, and World Cup fixtures.
- The Data Science layer provides match prediction functionality through trained model artifacts and `src/predict.py`.
- The Assistant layer connects these assets through a simple router, tool functions, and response formatters.

## Feature Overview

The current assistant supports five core capabilities.

| Capability | Description | Example User Questions |
| --- | --- | --- |
| Team Elo lookup | Retrieves a team's latest Elo rating, rank, and snapshot date. | "What is Belgium's Elo rating?", "What is the Elo rating for Brazil?" |
| Team group lookup | Retrieves the team's World Cup group, confederation, and FIFA rank. | "What group is France in?", "Which group is Argentina in?" |
| Team fixture lookup | Lists the team's known World Cup 2026 fixtures. | "Show fixtures for Morocco", "Fixtures for Japan" |
| Team comparison | Compares two teams using Elo rating and Elo rank. | "Compare Belgium and Egypt", "Compare Spain and Germany" |
| Match prediction | Predicts match outcome probabilities for two teams. | "Predict France vs Germany", "Predict Brazil vs Argentina" |

## Architecture

The assistant follows a tool-based request-response flow. A user question is routed to a football data or prediction tool, resolved using processed datasets or model prediction logic, and formatted into a user-facing response.

The current codebase includes two routing approaches:

- A deterministic rule-based route in `assistant.py`, useful for simple local testing.
- An experimental local LLM router in `router.py`, using Ollama and `llama3.2:1b` to select the most appropriate tool.

```text
User Question
    |
    v
Assistant Router
(Rule-Based or Local LLM)
    |
    v
Tool Selection
    |
    v
Data Retrieval / Model Prediction
    |
    v
Formatter
    |
    v
Response
```

At a high level, the assistant separates responsibilities into three layers:

- `assistant.py` handles the rule-based terminal assistant flow.
- `router.py` handles local LLM-based tool selection.
- `tools.py` handles data access and prediction calls.
- `formatters.py` converts tool outputs into readable responses.

## Project Structure

The assistant-related source code is located in `src/assistant/`.

```text
src/assistant/
├── assistant.py
├── router.py
├── tools.py
└── formatters.py
```

### `assistant.py`

`assistant.py` contains the main assistant entry point. It defines `ask_assistant(question)`, converts the question to lowercase, and uses simple keyword checks to decide which tool should answer the request.

It currently routes questions based on terms such as:

- `elo`
- `group`
- `fixture`
- `compare`
- `predict`

The file also includes a basic terminal loop under `if __name__ == "__main__":`, allowing the assistant to be tested interactively from the command line.

### `router.py`

`router.py` contains the experimental local LLM router. It sends a constrained prompt to an Ollama model and asks the model to return exactly one tool name.

This layer is responsible for intent detection only. It does not retrieve data or execute tools directly.

Current model:

```text
llama3.2:1b
```

### `tools.py`

`tools.py` contains the assistant's operational functions. These functions load processed CSV datasets, filter records for requested teams, compare team ratings, and call the prediction pipeline.

This file is responsible for:

- Loading processed datasets from `data/processed/`.
- Returning structured dictionaries from each tool.
- Calling `predict_match()` from `src/predict.py` for match prediction.

### `formatters.py`

`formatters.py` contains response formatting functions. Each formatter receives a structured dictionary from a tool and converts it into a readable text response.

This keeps data retrieval separate from presentation logic and makes the assistant easier to extend.

## Available Tools

### `get_team_elo(team)`

**Purpose**

Retrieves the latest Elo information for a specific World Cup 2026 team.

**Data source**

`data/processed/elo_latest.csv`

**Returned information**

- Team name
- Elo rating
- Elo rank
- Elo snapshot date
- Found/not found status

**Example question**

```text
What is Belgium's Elo rating?
```

### `get_team_group(team)`

**Purpose**

Retrieves World Cup 2026 team metadata, including the team's group assignment.

**Data source**

`data/processed/wc_2026_teams_cleaned.csv`

**Returned information**

- Team name
- World Cup group
- Confederation
- FIFA rank
- Found/not found status

**Example question**

```text
What group is France in?
```

### `get_team_fixtures(team)`

**Purpose**

Retrieves the known World Cup 2026 fixtures for a selected team.

**Data source**

`data/processed/wc_2026_fixtures_enriched.csv`

**Returned information**

- Team name
- Fixture opponent
- Match stage
- Match date
- Found/not found status

**Example question**

```text
Show fixtures for Brazil
```

### `compare_teams(team1, team2)`

**Purpose**

Compares two teams using their latest Elo ratings and ranks.

**Data source**

`data/processed/elo_latest.csv`

**Returned information**

- Team 1 name, Elo rating, and Elo rank
- Team 2 name, Elo rating, and Elo rank
- Elo difference
- Stronger team based on Elo rating
- Found/not found status

**Example question**

```text
Compare Belgium and Egypt
```

### `get_match_prediction(home, away)`

**Purpose**

Generates match outcome probabilities for a selected home team and away team.

**Prediction models used**

- XGBoost classification model
- Poisson goal model
- Simple ensemble of both model outputs

**Returned information**

- Home team
- Away team
- Home win probability
- Draw probability
- Away win probability
- Favorite outcome
- Found/not found status

**Example question**

```text
Predict France vs Germany
```

## Data Sources

The assistant uses processed datasets created by the project pipeline.

### `elo_latest.csv`

This dataset stores the latest Elo snapshot for World Cup 2026 teams. It is used by Elo lookup and team comparison tools.

Main role:

- Provides team strength indicators.
- Supports ranking-based comparisons.
- Supplies rating data used in the prediction layer.

### `wc_2026_teams_cleaned.csv`

This dataset stores cleaned World Cup 2026 team metadata.

Main role:

- Provides team names in standardized form.
- Stores group assignments.
- Stores confederation and FIFA ranking information.

### `wc_2026_fixtures_enriched.csv`

This dataset stores enriched World Cup 2026 fixture information.

Main role:

- Provides known fixtures by team.
- Supports fixture lookup questions.
- Connects teams, dates, stages, and enriched match context.

## Prediction Integration

The assistant integrates with the prediction layer through `src.predict.predict_match`.

The `get_match_prediction(home, away)` tool calls `predict_match(home, away)` and converts the result into a structured dictionary for formatting.

At a high level, `predict.py` combines two approaches:

- **XGBoost model**: A supervised classification model that predicts match outcome probabilities from engineered team and match features.
- **Poisson model**: A goal-based model that estimates expected goals for both teams and converts those estimates into outcome probabilities.
- **Ensemble prediction**: The final prediction averages the XGBoost and Poisson probability outputs to produce one set of match outcome probabilities.

The assistant does not implement the model logic directly. It acts as a user-facing interface over the prediction function.

## Current Limitations

The current assistant is intentionally simple and works as a first functional prototype.

Known limitations:

- The original terminal assistant still relies on `if` / `elif` keyword routing.
- The local LLM router currently returns only the tool name.
- Team extraction and tool argument parsing are still simple.
- Questions work best when they follow expected football patterns.
- There is no conversational memory between questions.
- There is no full agentic multi-step workflow yet.
- There is no Retrieval-Augmented Generation implementation.
- There is no assistant web interface yet.
- The assistant does not perform fuzzy matching for misspelled team names.
- The assistant depends on local processed datasets and trained prediction model files being available.
- Local LLM routing requires Ollama to be installed and running.

## Product Roadmap

This roadmap summarizes the feature direction. For the detailed version-by-version implementation journal, see [`ai_assistant_progress_report.md`](ai_assistant_progress_report.md).

### Near Term

- Dynamic team extraction from project datasets
- Structured LLM outputs with tool arguments
- Better error messages for unknown teams or unsupported questions
- More flexible parsing of team names

### Mid Term

- Streamlit chat interface
- Additional football analytics tools
- Group-level summaries
- Fixture difficulty analysis
- Team form summaries
- Basic tournament path analysis

### Long Term

- Conversation memory
- RAG over project documentation
- Power BI integration
- Model explanation assistant
- Multi-tool orchestration
- Cross-source analytical answers combining fixtures, Elo, groups, and predictions

## Conclusion

The World Cup Assistant demonstrates how a Data Engineering and Data Science project can be extended into an AI-style user interface.

It shows Data Engineering through its use of cleaned and enriched processed datasets. It shows Data Science integration through the match prediction workflow built on top of XGBoost and Poisson models. It shows Software Engineering through modular separation between routing, tools, and formatting. Finally, it introduces AI Assistant architecture by creating a tool-based natural language interface that can later evolve into an LLM-powered agent.

As a portfolio feature, the assistant is a strong bridge between data pipelines, predictive modeling, and user-facing AI product design.
