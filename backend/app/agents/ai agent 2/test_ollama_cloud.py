
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OLLAMA_API_KEY")
model = os.getenv("OLLAMA_MODEL", "beam:cloud")

if not api_key:
    raise ValueError(
        "OLLAMA_API_KEY is missing. Check your .env file."
    )

url = "https://ollama.com/api/chat"

payload = {
    "model": model,
    "messages": [
        {
            "role": "user",
            "content": (
                "Reply with exactly: "
                "Agent 2 cloud connection successful."
            ),
        }
    ],
    "stream": False,
}

response = requests.post(
    url,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json=payload,
    timeout=120,
)

if not response.ok:
    print("Request failed:", response.status_code)
    print(response.text)
    response.raise_for_status()

data = response.json()
print(data["message"]["content"])
