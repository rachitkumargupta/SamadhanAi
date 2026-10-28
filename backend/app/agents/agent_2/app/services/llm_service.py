
import requests
from ..config import settings
class LLMService:
    """Client for the hosted Ollama Cloud chat API."""
    def __init__(self) -> None:
        self.api_key = settings.ollama_api_key
        self.model = settings.ollama_model
        self.url = settings.ollama_chat_url
        self.timeout = settings.llm_timeout_seconds
        if not self.api_key:
            raise ValueError("OLLAMA_API_KEY is not configured in .env.")
    def chat(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        try:
            response = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            raise RuntimeError("Ollama Cloud request timed out.") from exc
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            raise RuntimeError(f"Ollama Cloud returned HTTP status {status_code}.") from exc
        except requests.RequestException as exc:
            raise RuntimeError("Could not connect to Ollama Cloud.") from exc
        except ValueError as exc:
            raise RuntimeError("Ollama Cloud returned an invalid JSON response.") from exc
        content = data.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Ollama Cloud returned an empty or invalid message.")
        return content.strip()
