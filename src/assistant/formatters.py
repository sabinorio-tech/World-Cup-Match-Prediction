def format_elo(result: dict) -> str:

    if not result["found"]:
        return result["message"]

    return (
        f"{result['team']} has an Elo rating of "
        f"{result['elo_rating']} "
        f"(World Rank #{result['elo_rank']}).\n"
        f"Snapshot date: {result['snapshot_date']}"
    )


def format_group(result: dict) -> str:

    if not result["found"]:
        return result["message"]

    return (
        f"{result['team']} is in Group {result['group']}.\n"
        f"Confederation: {result['confederation']}.\n"
        f"FIFA Rank: {result['fifa_rank']}."
    )


def format_fixtures(result: dict) -> str:

    if not result["found"]:
        return result["message"]

    lines = [f"Fixtures for {result['team'].title()}:\n"]

    for fixture in result["fixtures"]:
        lines.append(
            f"- {fixture['date']} | "
            f"{fixture['opponent']} | "
            f"{fixture['stage']}"
        )

    return "\n".join(lines)


def format_comparison(result: dict) -> str:

    if not result["found"]:
        return result["message"]

    return (
        f"{result['team1']['name']} "
        f"({result['team1']['elo_rating']}) vs "
        f"{result['team2']['name']} "
        f"({result['team2']['elo_rating']})\n\n"
        f"Elo Difference: {result['elo_difference']}\n"
        f"Stronger Team: {result['stronger_team']}"
    )

def format_prediction(result: dict) -> str:
    if not result["found"]:
        return result["message"]

    favorite_label = {
        "home_win": result["home_team"],
        "away_win": result["away_team"],
        "draw": "Draw"
    }[result["favorite"]]

    return (
        f"Prediction: {result['home_team']} vs {result['away_team']}\n\n"
        f"- {result['home_team']} win: {result['home_win']:.1%}\n"
        f"- Draw: {result['draw']:.1%}\n"
        f"- {result['away_team']} win: {result['away_win']:.1%}\n\n"
        f"Favorite: {favorite_label}"
    )