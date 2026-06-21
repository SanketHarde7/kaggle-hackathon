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
from app.context.project_scanner import detect_project_context
from app.memory.store import add_decision

router = APIRouter()

@router.post("/analyze", response_model=DecisionResponse)
async def analyze_decision_route(request: DecisionRequest):
    ensure_provider_configured()
    
    provider = get_provider(settings.llm_provider, settings.llm_api_key)
    
    # Auto-detect context
    project_context = detect_project_context(request.workspace_path)
    
    # Merge with manual context (manual wins)
    if request.manual_context:
        project_context["manual_context"] = request.manual_context
        project_context["context_override_note"] = "User provided manual context which MUST take precedence over detected auto-context if there are conflicts."
    
    # Also add the workspace path explicitly so the LLM knows
    project_context["workspace_path"] = request.workspace_path
    
    try:
        research_findings = await run_research(request.query, project_context, provider)
        brief = await analyze_decision(
            request.query, project_context, research_findings, provider
        )
        
        # Save decision to memory
        add_decision(request.workspace_path, request.query, research_findings, brief)
        
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

