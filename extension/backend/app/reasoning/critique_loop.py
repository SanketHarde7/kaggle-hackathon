"""
New 2-call reasoning engine for StackDecide.

Call 1 — extract_decisions_and_plan_queries():
    Identifies distinct decisions from the user prompt, checks for domain mismatches,
    and generates exactly 2 search queries per non-mismatched decision.

Call 2 — score_and_decide():
    Receives research findings for every decision and produces scored results in a
    single LLM call (not one per decision).

Call 3 — generate_annotated_prompt():
    Pure string templating — appends a "Consider this" block to the original prompt.
    Zero LLM calls; no rate-limit exposure.
"""

import asyncio
import json
import logging
from app.providers.base import LLMProvider
from app.models.schemas import (
    DecisionBrief,
    DecisionResult,
    ExtractionResult,
    OptionScore,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _parse_json_from_llm(text: str) -> dict:
    """
    Defensively strip markdown fences and parse JSON from LLM output.

    Args:
        text (str): The raw string output from the LLM.

    Returns:
        dict: The parsed JSON dictionary.
    """
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Call 1 — Decision Extraction + Query Planning
# ---------------------------------------------------------------------------

async def extract_decisions_and_plan_queries(
    user_prompt: str,
    project_context: dict,
    memory_context: str,
    provider: LLMProvider,
) -> ExtractionResult:
    """
    Single LLM call that:
    1. Identifies every distinct technical decision in the user prompt.
    2. Performs context-mismatch detection up front.
    3. Generates exactly 2 search queries per non-mismatched decision.

    Args:
        user_prompt (str): The initial query from the user.
        project_context (dict): The auto-detected and manual context of the workspace.
        memory_context (str): History of past decisions in this workspace.
        provider (LLMProvider): The LLM client instance.

    Returns:
        ExtractionResult: A structured object containing decisions, queries, and mismatches.
    """
    context_summary = json.dumps(project_context, indent=2)
    sibling_info = ""
    if project_context.get("sibling_projects_detected"):
        sibling_info = f"\nDetected sibling projects: {project_context['sibling_projects_detected']}"

    prompt = f"""You are a senior software architect analyzing a developer's request.

USER PROMPT:
{user_prompt}

AUTO-DETECTED PROJECT CONTEXT:
{context_summary}{sibling_info}

PAST DECISIONS IN THIS PROJECT:
{memory_context if memory_context else "(none yet)"}

Your task has three parts:

PART A — IDENTIFY DECISIONS
List every distinct technical decision implied by the user prompt. A direct question like "Zustand or Redux?" is one decision: ["state management"]. A larger spec might yield multiple: ["authentication method", "real-time sync mechanism", "database choice"].
STRICT REQUIREMENT: You must ONLY extract decisions if the user's
 prompt is explicitly asking about or discussing software architecture, libraries,
  frameworks, coding patterns, or technical infrastructure. If the prompt is conversational
   (e.g., "hello", "how are you"), general, non-technical, or ambiguous, you MUST return an empty list: [].
 Do not hallucinate or force a technical decision if none is clearly asked for.

PART B — CONTEXT MISMATCH CHECK
For each identified decision, check whether its domain is compatible with the detected project context.
- If the project is a pure Python backend (FastAPI, Flask, etc.) and the decision is about JavaScript frontend libraries (React state management, CSS frameworks, etc.), that is a mismatch — flag it, cross-reference sibling projects if detected.
- If no relevant sibling project was found, explicitly say the question doesn't apply to this workspace.
- Only flag genuine mismatches. Do NOT flag decisions that could plausibly apply to any tech stack.

PART C — SEARCH QUERIES
For each decision that is NOT mismatched, generate EXACTLY 2 search queries:
- Query 1: A direct comparison query (e.g., "Zustand vs Redux 2024 comparison")
- Query 2: A recency or ecosystem query (e.g., "Redux adoption trends developer sentiment 2024")
Use your judgment to craft the best queries for the specific decision — these are not rigid templates.

IMPORTANT: Do NOT generate queries for decisions that have a mismatch_warning.

Return ONLY a valid JSON object with this exact structure (no markdown fences):
{{
  "decisions": ["decision topic 1", "decision topic 2"],
  "queries": {{
    "decision topic 1": ["query one", "query two"],
    "decision topic 2": ["query one", "query two"]
  }},
  "mismatch_warnings": {{
    "decision topic X": "Explanation of mismatch, referencing sibling projects if applicable"
  }}
}}

The mismatch_warnings object should ONLY contain keys for decisions that actually have a mismatch. Omit keys for decisions with no mismatch. If no mismatches, use an empty object {{}}.
Do NOT include mismatched decisions in the queries object."""

    response = await provider.generate(prompt)

    try:
        data = _parse_json_from_llm(response)
        return ExtractionResult(**data)
    except Exception as e:
        logger.warning(f"Call 1 JSON parsing failed: {e}. Raw: {response[:300]}")
        # Minimal fallback: assume no decisions found
        return ExtractionResult(
            decisions=[],
            queries={},
            mismatch_warnings={}
        )


# ---------------------------------------------------------------------------
# Call 2 — Scoring + Decision (batched for large sets)
# ---------------------------------------------------------------------------

# Each decision's Tavily "advanced" research text can reach ~3-4k tokens.
# Groq free-tier has a 12k TPM limit.  With system prompt (~1.5k tokens) +
# scoring instructions (~1k) + output headroom, that leaves ~8-9k for
# research text.  At batch size 2 with truncation to 1500 chars per
# decision: ~2×1500/4 ≈ 750 tokens of research + 2.5k overhead = ~3.3k per
# batch, comfortably within limits.  Size 3 exceeded 13k in real tests.
MAX_DECISIONS_PER_SCORING_CALL = 2
MAX_RESEARCH_CHARS_PER_DECISION = 1500  # truncate to keep batch within TPM


async def _score_batch(
    batch: list[str],
    user_prompt: str,
    project_context: dict,
    research_by_decision: dict[str, str],
    provider: LLMProvider,
) -> list[DecisionResult]:
    """
    Score a single batch of decisions in one LLM call.

    Args:
        batch (list[str]): The subset of decisions to score in this batch.
        user_prompt (str): The original user prompt.
        project_context (dict): The workspace context.
        research_by_decision (dict[str, str]): Cleaned research text keyed by decision.
        provider (LLMProvider): The LLM client instance.

    Returns:
        list[DecisionResult]: The scored results for this batch.
    """
    research_sections = ""
    for dec in batch:
        research_text = research_by_decision.get(dec, "(no research available)")
        # Truncate to keep within token limits
        if len(research_text) > MAX_RESEARCH_CHARS_PER_DECISION:
            research_text = research_text[:MAX_RESEARCH_CHARS_PER_DECISION] + "\n... (truncated)"
        research_sections += f"\n### Decision: {dec}\n{research_text}\n"

    prompt = f"""You are a senior software architect producing scored technology decisions.

USER PROMPT:
{user_prompt}

PROJECT CONTEXT:
{json.dumps(project_context, indent=2)}

RESEARCH FINDINGS (by decision topic):
{research_sections}

For EACH decision topic listed below, produce a structured scoring of the realistic options.

DECISIONS TO SCORE:
{json.dumps(batch, indent=2)}

For each decision:
1. Identify the realistic options being compared (derive from the user prompt and research).
2. Score each option 0-10 on EXACTLY these 4 dimensions:
   - performance: raw speed, throughput, resource efficiency
   - maintainability: code complexity, documentation quality, ecosystem maturity
   - cost: free tier availability, pricing at scale, hidden costs
   - project_fit: how well it integrates with the detected project stack and constraints
3. Compute total_score as the SUM of the 4 dimension scores (scale: 0-40).
4. Write one concise why_chosen_over_others string (1-2 sentences) per option — focus on WHY this option compares favorably or unfavorably against the others specifically, not generic description.
5. Set final_pick to the option with the highest total_score (ties broken by project_fit).

Return ONLY a valid JSON array (no markdown fences):
[
  {{
    "decision_topic": "exact topic string from DECISIONS TO SCORE",
    "options_considered": ["Option A", "Option B"],
    "scores": [
      {{
        "option_name": "Option A",
        "performance": 8,
        "maintainability": 7,
        "cost": 9,
        "project_fit": 8,
        "total_score": 32,
        "why_chosen_over_others": "..."
      }},
      {{
        "option_name": "Option B",
        "performance": 6,
        "maintainability": 8,
        "cost": 7,
        "project_fit": 6,
        "total_score": 27,
        "why_chosen_over_others": "..."
      }}
    ],
    "final_pick": "Option A",
    "mismatch_warning": null
  }}
]"""

    response = await provider.generate(prompt)
    raw_results = _parse_json_from_llm(response)
    if not isinstance(raw_results, list):
        raise ValueError("Expected a JSON array from Call 2 batch")

    results = []
    for item in raw_results:
        scores = [OptionScore(**s) for s in item.get("scores", [])]
        results.append(DecisionResult(
            decision_topic=item["decision_topic"],
            options_considered=item.get("options_considered", []),
            scores=scores,
            final_pick=item.get("final_pick"),
            mismatch_warning=None,
        ))
    return results


async def score_and_decide(
    user_prompt: str,
    project_context: dict,
    decisions: list[str],
    research_by_decision: dict[str, str],
    mismatch_warnings: dict[str, str],
    provider: LLMProvider,
) -> list[DecisionResult]:
    """
    Score all non-mismatched decisions.  When decision count exceeds
    MAX_DECISIONS_PER_SCORING_CALL, splits into concurrent batches so no
    single call is too large for free-tier token limits.

    Args:
        user_prompt (str): The original user prompt.
        project_context (dict): The workspace context.
        decisions (list[str]): List of all extracted decisions.
        research_by_decision (dict[str, str]): Cleaned research text for valid decisions.
        mismatch_warnings (dict[str, str]): Dict of warnings for invalid decisions.
        provider (LLMProvider): The LLM client instance.

    Returns:
        list[DecisionResult]: The final aggregated and ordered list of decision results.
    """
    scoreable = [d for d in decisions if d not in mismatch_warnings]
    results: list[DecisionResult] = []

    if scoreable:
        # Split into batches
        batches = [
            scoreable[i : i + MAX_DECISIONS_PER_SCORING_CALL]
            for i in range(0, len(scoreable), MAX_DECISIONS_PER_SCORING_CALL)
        ]
        logger.info(
            f"Call 2: scoring {len(scoreable)} decisions in {len(batches)} batch(es) "
            f"(sizes: {[len(b) for b in batches]})"
        )

        # Run all batches concurrently
        batch_tasks = [
            _score_batch(batch, user_prompt, project_context, research_by_decision, provider)
            for batch in batches
        ]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        for i, res in enumerate(batch_results):
            if isinstance(res, Exception):
                logger.warning(f"Call 2 batch {i+1}/{len(batches)} failed: {res}")
                # Don't silently drop — produce explicit failure stubs
                for dec in batches[i]:
                    results.append(DecisionResult(
                        decision_topic=dec,
                        options_considered=[],
                        scores=[],
                        final_pick=None,
                        mismatch_warning=f"Scoring could not be completed (batch {i+1} failed: {res}). Please retry this decision.",
                    ))
            else:
                results.extend(res)

    # Append mismatched decisions with no scoring
    for dec, warning in mismatch_warnings.items():
        results.append(DecisionResult(
            decision_topic=dec,
            options_considered=[],
            scores=[],
            final_pick=None,
            mismatch_warning=warning,
        ))

    # Return in original decision order
    order = {d: i for i, d in enumerate(decisions)}
    results.sort(key=lambda r: order.get(r.decision_topic, 999))
    return results


# ---------------------------------------------------------------------------
# Call 3 — Annotated Prompt (pure templating, zero LLM calls)
# ---------------------------------------------------------------------------

def generate_annotated_prompt(original_prompt: str, results: list[DecisionResult]) -> str:
    """
    Appends a 'Consider this when implementing' block to the original prompt,
    or returns a clarification message if all decisions were context mismatches.

    Args:
        original_prompt (str): The exact text the user submitted.
        results (list[DecisionResult]): The list of scored decisions.

    Returns:
        str: The fully annotated string to be passed back to the user or IDE.
    """
    if not results:
        return f'I asked: "{original_prompt}"\n\nStackDecide couldn\'t identify any technical decisions in this prompt. Please ask a technical question or provide a project specification.'

    if results and all(r.mismatch_warning for r in results):
        lines = [
            f'I asked: "{original_prompt}"',
            "",
            "StackDecide couldn't produce an actionable recommendation — every part of this request appears to be a context mismatch:"
        ]
        for r in results:
            lines.append(f"- {r.decision_topic}: {r.mismatch_warning}")
        lines.extend([
            "",
            "Before implementing anything, please clarify or point StackDecide at the right part of your project."
        ])
        return "\n".join(lines)

    lines = [original_prompt, "", "---", "Consider this when implementing:"]
    for r in results:
        if r.mismatch_warning:
            lines.append(
                f"- {r.decision_topic}: flagged as not applicable — {r.mismatch_warning}"
            )
        else:
            best = next((s for s in r.scores if s.option_name == r.final_pick), None)
            why = best.why_chosen_over_others if best else ""
            # Trim why to ~100 chars for compactness
            why_short = (why[:97] + "...") if len(why) > 100 else why
            lines.append(f"- {r.decision_topic}: {r.final_pick} ({why_short})")
    return "\n".join(lines)
