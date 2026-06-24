import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "mistral",
        "prompt": "What is the capital of Belgium?",
        "stream": False,
    },
)

print(response.status_code)
print(response.text)