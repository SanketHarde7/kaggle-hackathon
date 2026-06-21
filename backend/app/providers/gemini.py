import httpx
from app.providers.base import LLMProvider, ProviderResponseError, handle_httpx_errors

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        super().__init__(api_key)
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    async def generate(self, prompt: str) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.url,
                    params={"key": self.api_key},
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderResponseError(f"Failed to parse Gemini response: {e}")
        except Exception as e:
            handle_httpx_errors(e)
            raise
