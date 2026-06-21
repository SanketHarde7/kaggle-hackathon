import httpx
from app.providers.base import LLMProvider, ProviderResponseError, handle_httpx_errors

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        super().__init__(api_key)
        self.model = model
        self.url = "https://api.anthropic.com/v1/messages"

    async def generate(self, prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                return data["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderResponseError(f"Failed to parse Claude response: {e}")
        except Exception as e:
            handle_httpx_errors(e)
            raise
