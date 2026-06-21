from fastapi import APIRouter, HTTPException
from app.models.schemas import DecisionRequest, DecisionResponse
from app.config import settings, ensure_provider_configured
from app.providers.factory import get_provider
from app.providers.base import (
    ProviderAuthError, ProviderRateLimitError, 
    ProviderTimeoutError, ProviderResponseError
)
from app.research.orchestrator import run_research
from app.reasoning.critique_loop import analyze_decision

router = APIRouter()

@router.post("/analyze", response_model=DecisionResponse)
async def analyze_decision_route(request: DecisionRequest):
    ensure_provider_configured()
    
    provider = get_provider(settings.llm_provider, settings.llm_api_key)
    project_context = {"workspace_path": request.workspace_path}
    if request.manual_context:
        project_context["manual_context"] = request.manual_context
    
    try:
        research_findings = await run_research(request.query, project_context, provider)
        brief = await analyze_decision(
            request.query, project_context, research_findings, provider
        )
        return DecisionResponse(brief=brief)
    except ProviderAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ProviderRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ProviderTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except ProviderResponseError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
