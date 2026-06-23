from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import runtime_settings, get_active_provider
from app.providers.factory import SUPPORTED_PROVIDERS

from typing import Optional

router = APIRouter()

class SettingsRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None

@router.post("/settings")
def update_settings(request: SettingsRequest):
    # Validate provider name if provided
    if request.provider is not None:
        provider_lower = request.provider.lower()
        if provider_lower not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=400, detail=f"Unknown LLM provider: {request.provider}. Supported providers: {list(SUPPORTED_PROVIDERS)}")
        runtime_settings["llm_provider"] = provider_lower

    if request.api_key is not None:
        runtime_settings["llm_api_key"] = request.api_key
    
    if request.tavily_api_key is not None:
        runtime_settings["tavily_api_key"] = request.tavily_api_key
    
    return {"status": "success", "message": "Settings saved"}

@router.get("/settings")
def get_settings():
    from app.config import get_active_tavily_key
    provider = get_active_provider()
    return {
        "provider": provider,
        "configured": provider is not None,
        "tavily_configured": get_active_tavily_key() is not None
    }
