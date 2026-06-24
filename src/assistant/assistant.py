from src.assistant.tools import (
    get_team_elo,
    get_team_group,
    get_team_fixtures,
    compare_teams,
    get_match_prediction,
)

from src.assistant.formatters import (
    format_elo,
    format_group,
    format_fixtures,
    format_comparison,
    format_prediction,
)

from src.assistant.router import choose_tool

def ask_assistant(question: str):

    question = question.lower()

    if "elo" in question:
        team = (
            question
            .replace("what is", "")
            .replace("what's", "")
            .replace("the", "")
            .replace("elo", "")
            .replace("rating", "")
            .strip()
        )
        return format_elo(get_team_elo(team))

    elif "group" in question:
        team = (
            question
            .replace("what group is", "")
            .replace("which group is", "")
            .replace("in", "")
            .strip()
        )
        return format_group(get_team_group(team))

    elif "fixture" in question:
        team = (
            question
            .replace("show", "")
            .replace("fixtures", "")
            .replace("fixture", "")
            .strip()
        )
        return format_fixtures(get_team_fixtures(team))

    elif "compare" in question:
        teams = question.replace("compare", "").split("and")

        if len(teams) == 2:
            return format_comparison(
                compare_teams(teams[0].strip(), teams[1].strip())
            )
    
    elif "predict" in question:
        teams = question.replace("predict", "").split("vs")

        if len(teams) == 2:
            return format_prediction(
                get_match_prediction(
                    teams[0].strip().title(),
                    teams[1].strip().title()
                )
            )

    return "Sorry, I don't understand that question yet."



def ask_ai_assistant(question: str):
    tool = choose_tool(question)

    print(f"Selected tool: {tool}")

    # temporary simple team extraction
    question_lower = question.lower()

    known_teams = [
        "belgium",
        "egypt",
        "iran",
        "new zealand",
        "argentina",
        "france",
        "brazil",
        "spain",
        "germany",
        "england",
        "portugal",
        "japan",
    ]

    found_teams = [
        team for team in known_teams
        if team in question_lower
    ]

    if tool == "get_team_elo" and len(found_teams) >= 1:
        return format_elo(
            get_team_elo(found_teams[0])
        )

    if tool == "get_team_group" and len(found_teams) >= 1:
        return format_group(
            get_team_group(found_teams[0])
        )

    if tool == "get_team_fixtures" and len(found_teams) >= 1:
        return format_fixtures(
            get_team_fixtures(found_teams[0])
        )

    if tool == "compare_teams" and len(found_teams) >= 2:
        return format_comparison(
            compare_teams(found_teams[0], found_teams[1])
        )

    if tool == "get_match_prediction" and len(found_teams) >= 2:
        return format_prediction(
            get_match_prediction(
                found_teams[0].title(),
                found_teams[1].title()
            )
        )

    return "I understood the tool, but I could not extract the needed team names yet."


if __name__ == "__main__":

    print("⚽ World Cup Assistant")
    print("Type 'quit' to exit.\n")

    while True:

        question = input("You: ")

        if question.lower() in ["quit", "exit"]:
            print("Assistant: Goodbye!")
            break

        response = ask_ai_assistant(question)

        print(f"\nAssistant: {response}\n")