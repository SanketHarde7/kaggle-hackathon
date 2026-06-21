from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import runtime_settings, get_active_provider
from app.providers.factory import SUPPORTED_PROVIDERS

router = APIRouter()

class SettingsRequest(BaseModel):
    provider: str
    api_key: str

@router.post("/settings")
def update_settings(request: SettingsRequest):
    # Validate provider name
    provider_lower = request.provider.lower()
    if provider_lower not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown LLM provider: {request.provider}. Supported providers: {list(SUPPORTED_PROVIDERS)}")
        
    runtime_settings["llm_provider"] = provider_lower
    runtime_settings["llm_api_key"] = request.api_key
    
    return {"status": "success", "message": "Settings saved"}

@router.get("/settings")
def get_settings():
    provider = get_active_provider()
    return {
        "provider": provider,
        "configured": provider is not None
    }
