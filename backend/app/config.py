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
    "llm_api_key": None
}

def get_active_provider() -> Optional[str]:
    return runtime_settings["llm_provider"] or settings.llm_provider

def get_active_api_key() -> Optional[str]:
    return runtime_settings["llm_api_key"] or settings.llm_api_key

def ensure_provider_configured() -> None:
    if not get_active_provider() or not get_active_api_key():
        raise HTTPException(
            status_code=400,
            detail="No LLM provider configured. Please set your API key in StackDecide settings."
        )
