from abc import ABC, abstractmethod
import httpx

class ProviderAuthError(Exception): pass
class ProviderRateLimitError(Exception): pass
class ProviderTimeoutError(Exception): pass
class ProviderResponseError(Exception): pass

class LLMProvider(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass

def handle_httpx_errors(e: Exception):
    if isinstance(e, httpx.TimeoutException):
        raise ProviderTimeoutError(f"Request timed out: {e}")
    elif isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        text = e.response.text.lower()
        if status in (401, 403) or (status == 400 and "api key" in text):
            raise ProviderAuthError(f"Authentication failed: {e.response.text}")
        elif status == 429:
            raise ProviderRateLimitError(f"Rate limited: {e.response.text}")
        else:
            raise ProviderResponseError(f"HTTP error {status}: {e.response.text}")
    elif isinstance(e, httpx.RequestError):
        raise ProviderResponseError(f"Network error: {e}")
