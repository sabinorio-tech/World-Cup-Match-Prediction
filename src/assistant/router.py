import requests


TOOLS = """
You are a strict tool router for a World Cup assistant.

Choose exactly one tool from this list:

- get_team_elo: use when the user asks how strong one team is, asks for Elo, rating, rank, or team strength.
- get_team_group: use when the user asks which group one team is in.
- get_team_fixtures: use when the user asks for matches, fixtures, schedule, opponents, or games for one team.
- compare_teams: use when the user asks to compare two teams, especially with the word compare.
- get_match_prediction: use when the user asks who would win, predict, favorite, probability, chance, or outcome between two teams.

Rules:
- If the question contains "compare", always choose compare_teams, even if it also contains "vs".
- If the question contains "vs", "win", "favorite", "predict", or "probability", choose get_match_prediction.
- If the question asks for a group, choose get_team_group.
- If the question asks for fixtures, matches, schedule, opponents, or games, choose get_team_fixtures.
- If the question asks how strong a team is, choose get_team_elo.

Respond with ONLY the tool name.
"""


def choose_tool(question: str) -> str:
    prompt = f"""
{TOOLS}

Question:
{question}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:1b",
            "prompt": prompt,
            "stream": False,
        },
    )

    data = response.json()


    if "response" not in data:
        return f"Ollama error: {data}"

    return data["response"].strip()