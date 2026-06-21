from app.providers.base import LLMProvider
from app.providers.gemini import GeminiProvider
from app.providers.claude import ClaudeProvider
from app.providers.gpt import GPTProvider
from app.providers.grok import GrokProvider
from app.providers.groq import GroqProvider
from app.providers.openrouter import OpenRouterProvider

def get_provider(provider_name: str, api_key: str) -> LLMProvider:
    providers = {
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
        "gpt": GPTProvider,
        "grok": GrokProvider,
        "groq": GroqProvider,
        "openrouter": OpenRouterProvider,
    }
    
    name_lower = provider_name.lower()
    if name_lower not in providers:
        raise ValueError(f"Unknown LLM provider: {provider_name}. Supported providers: {list(providers.keys())}")
        
    return providers[name_lower](api_key=api_key)
