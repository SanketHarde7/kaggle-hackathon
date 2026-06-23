import asyncio
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models.schemas import (
    DecisionRequest,
    DecisionResponse,
    DecisionBrief,
    ApprovalRequiredResponse,
)
from app.config import (
    ensure_provider_configured,
    ensure_tavily_configured,
    get_active_provider,
    get_active_api_key,
)
from app.providers.factory import get_provider
from app.providers.base import (
    ProviderAuthError, ProviderRateLimitError,
    ProviderTimeoutError, ProviderResponseError,
)
from app.research.search_client import search, SearchProviderAuthError
from app.research.cleaner import clean_results
from app.reasoning.critique_loop import (
    extract_decisions_and_plan_queries,
    score_and_decide,
    generate_annotated_prompt,
)
from app.context.project_scanner import detect_project_context
from app.memory.store import add_decision
from app.memory.context_builder import build_memory_context

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_DECISIONS_AUTO = 10


@router.post("/analyze")
async def analyze_decision_route(request: DecisionRequest):
    ensure_provider_configured()
    ensure_tavily_configured()

    provider = get_provider(get_active_provider(), get_active_api_key())

    # Auto-detect context
    project_context = detect_project_context(request.workspace_path)

    # Merge with manual context (manual wins)
    if request.manual_context:
        project_context["manual_context"] = request.manual_context
        project_context["context_override_note"] = (
            "User provided manual context which MUST take precedence over "
            "detected auto-context if there are conflicts."
        )

    project_context["workspace_path"] = request.workspace_path

    try:
        # --- Stage 0: Build memory context ---
        memory_context = build_memory_context(request.workspace_path, request.query)

        # =========================================================
        # CALL 1 — Extract decisions + plan queries
        # =========================================================
        extraction = await extract_decisions_and_plan_queries(
            user_prompt=request.query,
            project_context=project_context,
            memory_context=memory_context,
            provider=provider,
        )

        decisions = extraction.decisions
        queries_map = extraction.queries          # {decision -> [q1, q2]}
        mismatch_warnings = extraction.mismatch_warnings  # {decision -> warning}

        if not decisions:
            raise HTTPException(
                status_code=400,
                detail="No tech-stack related decisions or architecture questions were detected in your query. Please ask a technical question."
            )

        # =========================================================
        # CHECKPOINT — >10 decisions need explicit approval
        # =========================================================
        if len(decisions) > MAX_DECISIONS_AUTO and not request.proceed_anyway:
            return JSONResponse(
                content={
                    "requires_approval": True,
                    "decision_count": len(decisions),
                    "decisions": decisions,
                },
                status_code=200,
            )

        # =========================================================
        # WEB RESEARCH — concurrent across all decisions × 2 queries
        # (skip mismatched decisions entirely)
        # =========================================================
        async def run_single_search(decision: str, query: str):
            try:
                results = await search(query)
                for r in results:
                    r["query"] = query
                return decision, results
            except SearchProviderAuthError:
                raise
            except Exception:
                return decision, []

        search_tasks = []
        for decision in decisions:
            if decision in mismatch_warnings:
                continue  # skip — no research for mismatched decisions
            for q in queries_map.get(decision, []):
                search_tasks.append(run_single_search(decision, q))

        raw_search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Re-raise auth errors; aggregate everything else
        research_by_decision: dict[str, list] = {}
        for res in raw_search_results:
            if isinstance(res, SearchProviderAuthError):
                raise res
            if isinstance(res, Exception):
                continue
            decision, results = res
            research_by_decision.setdefault(decision, []).extend(results)

        # Clean research per decision
        cleaned_research: dict[str, str] = {}
        for decision, results in research_by_decision.items():
            cleaned_research[decision] = clean_results(results) if results else ""

        # =========================================================
        # CALL 2 — Score + Decide (all decisions in one LLM call)
        # =========================================================
        decision_results = await score_and_decide(
            user_prompt=request.query,
            project_context=project_context,
            decisions=decisions,
            research_by_decision=cleaned_research,
            mismatch_warnings=mismatch_warnings,
            provider=provider,
        )

        # =========================================================
        # CALL 3 — Annotated Prompt (pure templating, no LLM)
        # =========================================================
        annotated = generate_annotated_prompt(request.query, decision_results)

        brief = DecisionBrief(
            original_query=request.query,
            results=decision_results,
            annotated_prompt=annotated,
        )

        # =========================================================
        # MEMORY — one record per decision topic
        # =========================================================
        for dr in decision_results:
            add_decision(request.workspace_path, dr)

        return DecisionResponse(brief=brief)

    except SearchProviderAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
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


@router.post("/annotate")
async def annotate_prompt_route(request: DecisionRequest):
    """
    Pure string templating endpoint — returns an annotated version of the original prompt.
    Requires that /analyze has already been run (results come from memory).
    In practice, the extension calls this immediately after /analyze completes.
    """
    # The extension sends the brief directly from the analyze response.
    # Since we can't re-accept a DecisionBrief here without tying this endpoint
    # to a session, the annotated prompt is generated in /analyze and attached
    # to the DecisionBrief. See DecisionResponse — annotated_prompt field added below.
    raise HTTPException(status_code=501, detail="Use the annotated_prompt field in /analyze response.")
