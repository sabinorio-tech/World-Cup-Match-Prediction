import requests


def main() -> None:
    """Run the optional local Ollama connectivity check."""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": "What is the capital of Belgium?",
            "stream": False,
        },
        timeout=30,
    )
    response.raise_for_status()
    print(response.status_code)
    print(response.text)


if __name__ == "__main__":
    main()
