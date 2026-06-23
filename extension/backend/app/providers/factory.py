from app.providers.base import LLMProvider
from app.providers.gemini import GeminiProvider
from app.providers.claude import ClaudeProvider
from app.providers.gpt import GPTProvider
from app.providers.grok import GrokProvider
from app.providers.groq import GroqProvider
from app.providers.openrouter import OpenRouterProvider

_PROVIDERS = {
    "gemini": GeminiProvider,
    "claude": ClaudeProvider,
    "gpt": GPTProvider,
    "grok": GrokProvider,
    "groq": GroqProvider,
    "openrouter": OpenRouterProvider,
}

SUPPORTED_PROVIDERS = set(_PROVIDERS.keys())

def get_provider(provider_name: str, api_key: str) -> LLMProvider:
    name_lower = provider_name.lower()
    if name_lower not in _PROVIDERS:
        raise ValueError(f"Unknown LLM provider: {provider_name}. Supported providers: {list(SUPPORTED_PROVIDERS)}")
        
    return _PROVIDERS[name_lower](api_key=api_key)
