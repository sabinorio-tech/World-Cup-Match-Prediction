# Dashboard Recommendations

## Objective

This document provides recommendations for the Data Analytics / Power BI team building the FIFA World Cup 2026 prediction dashboard.

The goal of the dashboard is to present match predictions, team strength, qualification chances, and tournament-level insights in a way that feels engaging for football fans and understandable for casual users.

This is not a technical Power BI implementation guide. It is a product and user-experience handoff from Data Engineering and Data Science to Data Analytics.

## Dashboard Philosophy

The dashboard should feel like a football analytics platform, not a traditional business reporting dashboard.

Prioritize:

- Match-centered storytelling
- Football-style cards
- Team badges, flags, and visual identity
- Clear probabilities
- Simple explanations of why a team is favored
- Interactive exploration
- Fast answers to fan-focused questions

Avoid:

- Large raw tables as the main experience
- Overly technical model terminology
- Dense KPI grids with no football context
- Visuals that require users to understand the data model before using the dashboard

The dashboard should help users answer questions such as:

- Who is likely to win this match?
- Which teams are tournament favorites?
- What are my country's chances?
- Which matches have upset potential?
- Who is likely to qualify from each group?
- What is a team's likely path through the tournament?

## Recommended Dashboard Pages

### Page 1: Tournament Overview

Purpose:

- Give users a quick understanding of the full tournament prediction picture.
- Highlight the biggest stories immediately.

Recommended visuals:

- Total matches
- Number of teams
- Average model confidence
- Highest win probability
- Biggest upset risk
- Top 10 strongest teams by Elo
- Tournament favorites
- Highest qualification probabilities
- Upcoming matches

Recommended presentation:

- Use football-style KPI cards rather than plain metric boxes.
- Show team names, flags, and short descriptions where possible.
- Include a small number of high-impact visuals instead of many small charts.

Example cards:

| Card | Example |
| --- | --- |
| Highest win probability | Spain 82% vs Saudi Arabia |
| Biggest upset risk | Japan vs Germany |
| Tournament favorite | Argentina 31% |
| Average confidence | 68% |

### Page 2: Match Prediction Center

Purpose:

- Let users explore individual match predictions.
- Make each match feel like a football preview.

Recommended layout:

- Team 1 card
- Team 2 card
- Central match prediction panel
- Win/draw/loss probability cards
- Predicted score
- Model confidence
- Key factors

Example match card:

```text
Belgium vs Egypt

Belgium Win: 42%
Draw: 29%
Egypt Win: 29%

Predicted Score:
2 - 1

Confidence:
Medium
```

Recommended key factors:

- Elo difference
- Recent form
- Goals scored
- Goals conceded
- Head-to-head record, if available
- Home/host or neutral-site context

User experience note:

- This page should avoid large tables. Users should feel like they are reading a match preview, not inspecting a spreadsheet.

### Page 3: Team Explorer

Purpose:

- Allow users to select a country and understand its tournament outlook.

Recommended visuals:

- Team summary card
- Elo rating
- FIFA ranking
- Recent form
- Last matches
- Goals scored
- Goals conceded
- Group-stage fixtures
- Predicted tournament finish
- Group qualification probability
- Tournament win probability

Recommended interactions:

- Team selector/slicer
- Group filter
- Confederation filter
- Toggle between team profile and fixture list

Fan-focused questions this page should answer:

- How strong is this team?
- Who are they playing?
- Are they expected to qualify?
- How far could they go?
- What are their strengths and weaknesses?

### Page 4: Group Stage Analysis

Purpose:

- Explain group standings and qualification predictions.

Recommended visuals:

- Group selector
- Predicted group table
- Predicted points
- Qualification chance
- Goals for
- Goals against
- Goal difference
- Remaining fixtures

Recommended presentation:

- Use one group at a time by default.
- Show qualification probability as progress bars or compact probability cards.
- Make the top qualifying teams visually clear.

Suggested group table fields:

| Field | Purpose |
| --- | --- |
| Team | Identifies each country in the group. |
| Predicted points | Shows expected group-stage performance. |
| Qualification probability | Shows chance of advancing. |
| Goals for | Summarizes attacking output. |
| Goals against | Summarizes defensive risk. |
| Goal difference | Gives a familiar football standings metric. |

### Page 5: Knockout Bracket

Purpose:

- Show possible tournament progression.
- Make the tournament path visually exciting.

Recommended content:

- Round of 32
- Round of 16
- Quarter Finals
- Semi Finals
- Final
- Winner

Recommended visuals:

- Bracket visualization
- Probability of reaching each round
- Probability of winning the tournament
- Favorite route to the final
- Upset markers for surprising projected winners

Design recommendation:

- This should be one of the most visually polished pages. Fans naturally understand tournament brackets, so the bracket should be central, readable, and interactive.

## Recommended KPIs

Recommended dashboard KPIs:

| KPI | Why it is useful |
| --- | --- |
| Total matches | Gives tournament scope. |
| Number of teams | Confirms tournament coverage. |
| Average model confidence | Summarizes how certain predictions are overall. |
| Highest win probability | Highlights the most one-sided predicted match. |
| Biggest upset risk | Adds drama and fan interest. |
| Top Elo teams | Shows underlying team strength. |
| Tournament win probability | Communicates favorites clearly. |
| Group qualification probability | Helps fans understand group-stage outlook. |
| Predicted score | Makes model output feel football-native. |
| Match confidence | Helps users interpret prediction reliability. |

## Recommended Filters

Filters should support exploration without making the dashboard feel like a database tool.

Recommended filters:

- Stage
- Group
- Team
- Confederation
- Match date
- Venue/country
- Prediction confidence
- Upset-risk level

Filter guidance:

- Put global filters on overview pages.
- Use team and match selectors on detailed pages.
- Avoid too many filters on a single screen.
- Always provide a clear reset option.
- Use filters to help users explore stories, not to force them to build their own report.

## Required Data Science Outputs

The dashboard will need prediction outputs from the Data Science team. These fields should be delivered in a clean, dashboard-ready dataset.

| Field | Purpose |
| --- | --- |
| `home_team` / `team1` | Identifies the first team in a match. |
| `away_team` / `team2` | Identifies the second team in a match. |
| `home_win_probability` / `team1_win_probability` | Main probability for team 1 winning. |
| `draw_probability` | Probability that the match ends in a draw. |
| `away_win_probability` / `team2_win_probability` | Main probability for team 2 winning. |
| `predicted_home_goals` / `predicted_team1_goals` | Makes predictions feel like football scorelines. |
| `predicted_away_goals` / `predicted_team2_goals` | Complements predicted score display. |
| `confidence_score` | Helps users understand prediction certainty. |
| `confidence_label` | User-friendly label such as Low, Medium, High. |
| `elo_difference` | Explains team-strength gap. |
| `recent_form_score` | Explains short-term team performance. |
| `group_qualification_probability` | Powers group-stage pages. |
| `round_reach_probability` | Powers knockout progression views. |
| `tournament_win_probability` | Powers tournament favorite visuals. |
| `upset_risk_score` | Helps identify matches where the favorite may be vulnerable. |

Recommended DS output principle:

- Data Science should provide probabilities and interpretable explanation fields.
- Data Analytics should focus on presentation, filtering, and storytelling.
- Feature engineering details should not be exposed directly unless they help explain predictions to users.

## User Experience Recommendations

### Prefer Cards Over Tables

Football fans usually want quick answers:

- Who wins?
- By how much?
- How confident is the prediction?
- Why is that team favored?

Cards are better suited than tables for these questions because they can combine team names, flags, probabilities, and short explanations in one readable unit.

### Use Match-Centric Design

The match should be the center of the experience.

Instead of starting from a dataset table, start from:

```text
Team A vs Team B
```

Then show:

- Win probabilities
- Predicted score
- Key factors
- Confidence
- Group or knockout context

This matches how fans think about football.

### Use Storytelling

Good dashboard storytelling can turn model outputs into understandable football narratives.

Examples:

- "Argentina are favorites because they have a large Elo advantage."
- "This match has upset potential because recent form is close."
- "Germany are likely to qualify, but the group remains competitive."

Use short labels and concise explanations. Avoid long technical descriptions.

### Use Football Visual Identity

Recommended visual elements:

- Country flags
- Team badges if available
- Football pitch textures or subtle football-themed backgrounds
- Bracket visuals
- Probability rings
- Progress bars
- Match cards

Color guidance:

- Use green for positive/team advantage indicators.
- Use amber/orange for uncertainty or upset risk.
- Use red sparingly for high-risk or negative signals.
- Ensure colors remain readable and accessible.

## Dashboard Mockup Inspiration

![FIFA World Cup 2026 dashboard mockup inspiration](assets/mockup%20world%20cup%20dashboard.png)

The provided mockup should be treated as design inspiration, not a strict implementation requirement.

Useful ideas from the mockup:

### Sidebar Navigation

The sidebar creates a product-like experience with clear page navigation:

- Overview
- Match Details
- Groups
- Knockout Bracket
- Teams
- About

This is preferable to a flat report with many disconnected pages.

### Tournament Overview Cards

The overview uses strong cards for:

- Total matches
- Average model confidence
- Highest win probability
- Biggest upset risk

This makes the dashboard feel modern and easy to scan.

### Match Prediction Cards

The match detail layout is effective because it puts the two teams and the prediction result at the center. The win/draw/loss probabilities are immediately visible and easy to understand.

### Team Rankings

The top-team ranking visual is useful for showing team strength without overwhelming users with raw Elo data.

Recommended display:

- Rank
- Flag
- Team
- Elo rating
- Compact strength bar

### Qualification Probability Visuals

Circular or bar-based probability visuals work well for group qualification and tournament win chances. They are easier for casual users to read than raw numeric tables.

### Knockout Bracket Visualization

The bracket page should be visually memorable. It should show possible progression through the tournament and make it easy to understand which teams are most likely to reach later rounds.

Recommended bracket elements:

- Team names and flags
- Match win probabilities
- Round reach probabilities
- Tournament winner probability
- Clear final/winner area

## Page Priority

Recommended build order:

1. Tournament Overview
2. Match Prediction Center
3. Group Stage Analysis
4. Team Explorer
5. Knockout Bracket

Reasoning:

- The overview and match pages provide the most immediate user value.
- Group analysis is important once qualification probabilities are available.
- Team explorer adds depth.
- Knockout bracket is visually valuable but depends on more advanced DS simulation outputs.

## Handoff Notes

The Data Analytics team should expect two types of model outputs:

- Match-level predictions
- Tournament simulation outputs

Match-level predictions power:

- Match cards
- Win/draw/loss probabilities
- Predicted scores
- Confidence indicators
- Upset risk

Tournament simulation outputs power:

- Group qualification probability
- Round reach probability
- Tournament win probability
- Knockout bracket paths

If tournament simulation outputs are not available immediately, the dashboard can still launch with:

- Tournament Overview
- Match Prediction Center
- Team Explorer
- Group Stage Analysis using available match probabilities

The knockout bracket page can be added once simulation outputs are ready.

## Final Recommendation

Build the dashboard around football questions, not around datasets.

The best version of this dashboard should feel like a prediction companion for the FIFA World Cup 2026: quick to understand, visually engaging, and easy for fans to explore before and during the tournament.
