from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import HTTPException

class Settings(BaseSettings):
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

def ensure_provider_configured() -> None:
    if not settings.llm_provider or not settings.llm_api_key:
        raise HTTPException(
            status_code=400,
            detail="No LLM provider configured. Please set your API key in StackDecide settings."
        )
