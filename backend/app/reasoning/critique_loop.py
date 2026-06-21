import asyncio
import json
import logging
import time
from app.providers.base import LLMProvider
from app.models.schemas import DecisionBrief

logger = logging.getLogger(__name__)

ANGLE_NAMES = [
    "performance_scalability",
    "maintainability_dev_effort",
    "cost_free_tier_feasibility",
    "project_fit",
]

ANGLE_DESCRIPTIONS = {
    "performance_scalability": "Performance and Scalability: Does the recommendation hold up if the project grows? Are there performance characteristics the draft ignored?",
    "maintainability_dev_effort": "Maintainability and Developer Effort: How much ongoing complexity/maintenance burden does this choice introduce, especially for a solo developer?",
    "cost_free_tier_feasibility": "Cost and Free-Tier Feasibility: Does this choice work within free-tier/low-budget constraints, or does it quietly assume paid infrastructure?",
    "project_fit": "Project Fit: Does this actually fit the specific project context (existing stack, stated constraints), or is it a generic 'best practice' answer that ignores what's already there?",
}


def _parse_json_from_llm(text: str) -> dict:
    """Defensively parse JSON from LLM output, stripping markdown fences."""
    cleaned = text.strip()
    # Strip markdown code fences
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    return json.loads(cleaned)


async def _stage1_initial_draft(
    user_query: str,
    project_context: dict,
    research_findings: str,
    provider: LLMProvider,
) -> str:
    """Stage 1: Generate initial recommendation draft."""
    prompt = f"""You are a senior software architect helping a developer make a technology decision.

USER QUERY: {user_query}

PROJECT CONTEXT:
{json.dumps(project_context, indent=2)}

RESEARCH FINDINGS (real-time web research):
{research_findings}

Based on the above research findings and project context, provide your initial recommendation.
Cover:
1. What options are being considered
2. Your preliminary recommendation
3. Key reasoning points
4. Notable tradeoffs

Write your response as a clear, detailed analysis. This is a first draft that will be critiqued from multiple angles before finalizing."""

    return await provider.generate(prompt)


async def _stage2_critique(
    angle_name: str,
    angle_description: str,
    user_query: str,
    project_context: dict,
    stage1_draft: str,
    provider: LLMProvider,
) -> dict:
    """Run a single critique from a specific angle."""
    prompt = f"""You are a critical reviewer analyzing a technology recommendation from a specific angle.

ANGLE TO CRITIQUE FROM: {angle_description}

ORIGINAL USER QUERY: {user_query}

PROJECT CONTEXT:
{json.dumps(project_context, indent=2)}

PRELIMINARY RECOMMENDATION (Stage 1 draft):
{stage1_draft}

Your task: Challenge the above recommendation from the {angle_description} perspective.
You MUST explicitly state whether you AGREE, PARTIALLY DISAGREE, or DISAGREE with the Stage 1 draft from this angle, and explain why.
Do not just restate the draft positively — be genuinely critical where warranted.

Respond with a concise but thorough critique (3-6 sentences)."""

    response = await provider.generate(prompt)
    return {"angle": angle_name, "critique": response}


async def _stage3_synthesis(
    user_query: str,
    project_context: dict,
    stage1_draft: str,
    critiques: list[dict],
    unavailable_angles: list[str],
    provider: LLMProvider,
) -> DecisionBrief:
    """Stage 3: Synthesize draft + critiques into final DecisionBrief."""
    critiques_text = ""
    for c in critiques:
        label = ANGLE_DESCRIPTIONS.get(c["angle"], c["angle"])
        critiques_text += f"\n### {label}\n{c['critique']}\n"

    unavailable_text = ""
    if unavailable_angles:
        labels = [ANGLE_DESCRIPTIONS.get(a, a) for a in unavailable_angles]
        unavailable_text = f"\nNOTE: The following critique angles could not be evaluated due to errors: {', '.join(labels)}. Acknowledge this in your angle_breakdown.\n"

    prompt = f"""You are a senior software architect producing a final technology decision brief.

ORIGINAL USER QUERY: {user_query}

PROJECT CONTEXT:
{json.dumps(project_context, indent=2)}

PRELIMINARY RECOMMENDATION (Stage 1):
{stage1_draft}

CRITIQUES FROM MULTIPLE ANGLES (Stage 2):
{critiques_text}
{unavailable_text}

Synthesize the preliminary recommendation with all critiques into a final decision brief.
Where critiques raised disagreements, explicitly resolve them (e.g., "the performance critique raised X concern; this is addressed/outweighed by Y").

Return ONLY a valid JSON object (no markdown fences, no extra text) with exactly this structure:
{{
  "options_considered": ["option1", "option2", ...],
  "final_recommendation": "The recommended choice and a brief justification",
  "reasoning_summary": "2-3 sentence summary of the overall reasoning",
  "angle_breakdown": {{
    "performance_scalability": "Brief note on this angle's assessment",
    "maintainability_dev_effort": "Brief note on this angle's assessment",
    "cost_free_tier_feasibility": "Brief note on this angle's assessment",
    "project_fit": "Brief note on this angle's assessment"
  }},
  "tradeoffs": ["tradeoff 1", "tradeoff 2", ...]
}}"""

    response = await provider.generate(prompt)

    try:
        data = _parse_json_from_llm(response)
        return DecisionBrief(**data)
    except Exception as e:
        logger.warning(f"Stage 3 JSON parsing failed: {e}. Attempting recovery.")
        # Fallback: try to build a DecisionBrief from what we have
        raise ValueError(f"Failed to parse final decision brief from LLM: {e}")


async def analyze_decision(
    user_query: str,
    project_context: dict,
    research_findings: str,
    provider: LLMProvider,
) -> DecisionBrief:
    """Full 3-stage reasoning pipeline: draft -> critique -> synthesis."""

    # Stage 1: Initial draft (sequential, required)
    logger.info("Stage 1: Generating initial draft...")
    stage1_start = time.time()
    stage1_draft = await _stage1_initial_draft(
        user_query, project_context, research_findings, provider
    )
    logger.info(f"Stage 1 completed in {time.time() - stage1_start:.2f}s")

    # Stage 2: Four-angle critique (concurrent, partial failure OK)
    logger.info("Stage 2: Running four-angle critique concurrently...")
    stage2_start = time.time()

    async def run_critique(angle_name: str):
        return await _stage2_critique(
            angle_name,
            ANGLE_DESCRIPTIONS[angle_name],
            user_query,
            project_context,
            stage1_draft,
            provider,
        )

    critique_tasks = [run_critique(name) for name in ANGLE_NAMES]
    critique_results = await asyncio.gather(*critique_tasks, return_exceptions=True)

    successful_critiques = []
    unavailable_angles = []
    for i, result in enumerate(critique_results):
        if isinstance(result, Exception):
            logger.warning(f"Critique angle '{ANGLE_NAMES[i]}' failed: {result}")
            unavailable_angles.append(ANGLE_NAMES[i])
        else:
            successful_critiques.append(result)

    stage2_elapsed = time.time() - stage2_start
    logger.info(
        f"Stage 2 completed in {stage2_elapsed:.2f}s "
        f"({len(successful_critiques)}/4 critiques succeeded)"
    )

    # Stage 3: Synthesis (sequential, requires Stage 1 + Stage 2)
    logger.info("Stage 3: Synthesizing final decision brief...")
    stage3_start = time.time()
    brief = await _stage3_synthesis(
        user_query,
        project_context,
        stage1_draft,
        successful_critiques,
        unavailable_angles,
        provider,
    )
    logger.info(f"Stage 3 completed in {time.time() - stage3_start:.2f}s")

    return brief
