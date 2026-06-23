from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import HTTPException

class Settings(BaseSettings):
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

runtime_settings = {
    "llm_provider": None,
    "llm_api_key": None,
    "tavily_api_key": None
}

def get_active_provider() -> Optional[str]:
    return runtime_settings.get("llm_provider") or settings.llm_provider

def get_active_api_key() -> Optional[str]:
    return runtime_settings.get("llm_api_key") or settings.llm_api_key

def get_active_tavily_key() -> Optional[str]:
    return runtime_settings.get("tavily_api_key") or settings.tavily_api_key

def ensure_provider_configured() -> None:
    if not get_active_provider() or not get_active_api_key():
        raise HTTPException(
            status_code=400,
            detail="No LLM provider configured. Please set your API key in StackDecide settings."
        )

def ensure_tavily_configured() -> None:
    if not get_active_tavily_key():
        raise HTTPException(
            status_code=400,
            detail="Tavily search API key not configured. Set it in StackDecide settings (or .env) to enable research."
        )
