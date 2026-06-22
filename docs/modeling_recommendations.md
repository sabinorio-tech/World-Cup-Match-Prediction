# Modeling Recommendations

## 1. Objective

The modeling objective is to predict FIFA World Cup 2026 match outcomes using cleaned historical international match results, Elo rating history, qualified-team metadata, and enriched World Cup 2026 fixture data.

Recommended prediction task:

```text
Given two national teams and match context, predict the match outcome.
```

The initial modeling scope should focus on 90-minute match outcomes:

- Home/team1 win
- Draw
- Away/team2 win

For the World Cup 2026 prediction layer, `team1` and `team2` should be treated as the two competing sides in the fixture. The model should not assume that `team1` has true home advantage unless a separate host/home-context feature is explicitly created.

## 2. Recommended Target Variable (Y)

Recommended target:

```text
outcome
```

The `results_historical.csv` dataset already contains an `outcome` column with three classes:

- `home_win`
- `draw`
- `away_win`

Why this target is appropriate:

- It is directly aligned with the match prediction goal.
- It is available for all completed historical matches.
- It supports a multiclass classification setup.
- It avoids predicting exact scores too early, which is a harder and noisier task.
- It can later be converted into probability outputs for dashboarding and match simulations.

Important modeling note:

Historical matches use `home_team` and `away_team`, while World Cup fixtures use `team1` and `team2`. A modeling dataset should define a consistent team-side convention before training and inference.

## 3. Candidate Features (X)

Candidate features should be developed in layers. The project should start with simple, explainable features, then add more advanced features only after a reliable baseline is established.

### Existing Features

Existing features are already available in the processed datasets and require minimal transformation.

From `wc_2026_fixtures_enriched.csv`:

- `stage`
- `group`
- `team1`
- `team2`
- `venue`
- `city`
- `country`
- `date`
- `kickoff_et`
- `is_placeholder_match`
- `team1_confederation`
- `team1_fifa_rank`
- `team1_coach`
- `team1_elo_rating`
- `team1_elo_rank`
- `team1_elo_country_code`
- `team1_elo_is_host`
- `team2_confederation`
- `team2_fifa_rank`
- `team2_coach`
- `team2_elo_rating`
- `team2_elo_rank`
- `team2_elo_country_code`
- `team2_elo_is_host`
- `team1_elo_snapshot_date`
- `team2_elo_snapshot_date`

From `results_historical.csv`:

- `date`
- `home_team`
- `away_team`
- `home_score`
- `away_score`
- `tournament`
- `city`
- `country`
- `neutral`
- `outcome`

From `elo_history.csv`:

- `snapshot_date`
- `country`
- `rank`
- `country_code`
- `rating`
- `confederation`
- `is_host`
- Historical match/stat summary fields such as wins, losses, draws, goals for, and goals against

### Engineered Features

Engineered features should be created after the baseline dataset is defined. These features should be computed in a time-aware way, using only information available before each historical match.

Recommended first-pass engineered features:

- Elo rating difference
- Elo rank difference
- FIFA rank difference for World Cup 2026 inference
- Neutral-site indicator
- Host-country indicator
- Same-confederation indicator
- Tournament type indicator
- Match year or era
- Team recent form before match date
- Goals scored per match before match date
- Goals conceded per match before match date
- Win/draw/loss rates before match date
- Days since previous match

### Advanced Features

Advanced features can be considered once the baseline model and validation strategy are stable.

Potential advanced features:

- Head-to-head record before match date
- Rolling Elo movement or rating momentum
- Rolling goal difference
- Strength-adjusted recent form
- Tournament-stage pressure indicators
- Confederation-vs-confederation historical performance
- Travel or venue-region features
- Squad/player-level features if reliable external data becomes available
- Simulation features for knockout-stage progression

Advanced features should be added incrementally and validated against a baseline to confirm that they improve generalization.

## 4. Feature Engineering Recommendations

### Elo Difference

Create the difference between the two teams' Elo ratings at the appropriate pre-match date.

Why useful:

- Captures relative team strength.
- Usually more informative than raw Elo values alone.
- Easy to explain and validate.

Leakage warning:

- For historical training, Elo must be joined using the latest snapshot available before the match date.

### FIFA Rank Difference

Create a rank difference between the two teams.

Why useful:

- Adds another external team-strength signal.
- May capture information not fully represented in Elo ratings.

Limitations:

- Current FIFA rankings in the team reference data are most useful for 2026 fixture inference.
- Historical FIFA rankings are not currently available in the processed data, so using static 2026 rankings for historical training would introduce leakage or inconsistency.

### Recent Form

Compute each team's recent results before the match date.

Examples:

- Points from last 5 matches
- Wins in last 5 matches
- Average goal difference in last 5 matches
- Goals scored/conceded in last 5 matches

Why useful:

- Captures short-term performance changes.
- Helps distinguish teams with similar long-term strength.

Leakage warning:

- Recent form must only use matches before the target match.

### Head-to-Head Statistics

Compute previous results between the two teams before the match date.

Examples:

- Previous meetings count
- Team1/head-side win rate
- Draw rate
- Average goals scored and conceded

Why useful:

- May capture matchup-specific patterns.

Limitations:

- Some teams have few or no prior meetings.
- Head-to-head features can be sparse and should not dominate the model.

### Goal-Scoring Metrics

Compute team attacking and defensive metrics before each match.

Examples:

- Goals scored per match
- Goals conceded per match
- Goal difference per match
- Clean-sheet rate
- Failed-to-score rate

Why useful:

- Adds football-specific performance signal.
- Complements outcome-only form features.

### Tournament Stage Indicators

Encode tournament and stage context.

Examples:

- Friendly vs competitive match
- FIFA World Cup match indicator
- Group stage vs knockout stage
- Neutral venue indicator

Why useful:

- Team behavior and match dynamics differ across contexts.
- World Cup matches may not behave like friendlies.

## 5. Potential Modeling Approaches

### Logistic Regression

Strengths:

- Strong baseline for multiclass classification.
- Fast to train.
- Interpretable coefficients.
- Useful for validating whether features have sensible directional effects.

Limitations:

- Assumes mostly linear relationships.
- May underfit complex football dynamics.

Recommended role:

- First baseline model.

### Random Forest

Strengths:

- Captures non-linear relationships.
- Handles mixed feature types after encoding.
- Provides feature-importance estimates.

Limitations:

- Can overfit if not tuned carefully.
- Probability calibration may be weaker than simpler models.
- Less efficient than gradient-boosted tree methods on larger feature sets.

Recommended role:

- Useful comparison model after a logistic regression baseline.

### XGBoost

Strengths:

- Strong tabular-data performance.
- Handles non-linear interactions well.
- Often performs well with engineered sports features.

Limitations:

- Requires careful tuning.
- Can overfit with leakage-prone or highly correlated features.
- Less interpretable than logistic regression.

Recommended role:

- Candidate production-grade model after baseline validation.

### LightGBM

Strengths:

- Efficient gradient-boosted tree implementation.
- Strong performance on structured tabular datasets.
- Handles larger datasets and many features efficiently.

Limitations:

- Requires careful validation and tuning.
- Can learn leakage quickly if time-aware feature construction is not strict.
- May need probability calibration depending on final use case.

Recommended role:

- Strong candidate for final tabular model comparison.

## 6. Validation Strategy

The validation strategy should respect historical chronology.

Recommended approach:

- Train on older matches.
- Validate on later matches.
- Test on the most recent historical period.
- Keep World Cup 2026 fixtures out of model training because they do not have known outcomes.

Avoid random train/test splits as the primary evaluation strategy. Random splits can leak future information into training and produce overly optimistic performance.

Recommended validation patterns:

- Time-based holdout split
- Rolling-origin validation
- Tournament-aware validation for major competitions

Data leakage controls:

- Do not use future match results to compute past team features.
- Do not use Elo snapshots after the match date.
- Do not use final tournament outcomes when predicting earlier tournament matches.
- Do not train on `results_future.csv`.
- Do not treat placeholder knockout fixtures as resolved teams.
- Do not use static 2026 team metadata as historical features unless the modeling design explicitly justifies it.

Evaluation should include:

- Accuracy
- Macro F1 score
- Log loss
- Confusion matrix
- Class-wise performance for home/team1 win, draw, and away/team2 win

If the final product displays probabilities, calibration should also be assessed.

## 7. Risks and Assumptions

Key risks:

- Football outcomes are noisy and difficult to predict.
- Draws may be harder to classify than wins.
- Historical data includes matches from many eras, and older matches may not reflect modern football.
- Friendly matches and competitive matches may have different dynamics.
- Team names and historical national entities may require careful handling in feature engineering.
- Elo history contains future snapshots, so incorrect joins can create leakage.
- Current FIFA rank and coach metadata may not be valid for historical training rows.
- Knockout-stage placeholders cannot be predicted as concrete matchups until tournament progression is simulated or resolved.

Assumptions:

- The cleaned Data Engineering datasets are trusted as the starting point.
- `results_historical.csv` is the source of labeled outcomes.
- `wc_2026_fixtures_enriched.csv` is the inference fixture dataset.
- Feature engineering will create training-time features separately from enrichment outputs.
- Predictions will initially target match outcome class, not exact scoreline.

## 8. Recommended Next Steps

Recommended next steps for the Data Science phase:

1. Define the modeling dataset schema.
2. Create a team-side convention that maps historical `home_team` / `away_team` to model-side team columns.
3. Implement time-aware feature generation under `src/features/`.
4. Build a simple baseline using Elo-derived features.
5. Add recent-form and goal-scoring features incrementally.
6. Establish a time-based train/validation/test split.
7. Compare Logistic Regression, Random Forest, XGBoost, and LightGBM.
8. Evaluate both classification performance and probability quality.
9. Document feature definitions and leakage safeguards.
10. Use the final trained pipeline to generate predictions for `wc_2026_fixtures_enriched.csv`.

The first modeling milestone should be a reliable baseline with clean validation, not maximum predictive complexity.
