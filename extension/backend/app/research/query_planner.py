import json
import logging
from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)

async def plan_queries(user_query: str, project_context: dict, provider: LLMProvider) -> list[str]:
    prompt = f"""
You are an expert technical researcher. The user wants to make a technology stack decision.
User Query: {user_query}
Workspace Context: {json.dumps(project_context)}

Break down the user's decision into 3 to 5 specific, well-formed search queries to gather real-time, current information from the web.
Rules for the queries:
1. Vary the angle of each query (e.g., direct comparison, recent trends/adoption, known problems/limitations, alternative options).
2. Include recency signals in at least some queries (e.g., mentioning the current year '2026') so results aren't dominated by outdated content.
3. Return ONLY a valid JSON array of strings. Do not include any other text, markdown fences (like ```json), or explanations.

Example output:
["React vs Vue performance 2026", "Vue 3 known limitations", "React server components community sentiment"]
"""
    response = await provider.generate(prompt)
    
    try:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
            
        queries = json.loads(cleaned.strip())
        if isinstance(queries, list) and len(queries) > 0 and all(isinstance(q, str) for q in queries):
            return queries[:5]
        else:
            raise ValueError("Parsed JSON is not a list of strings")
            
    except Exception as e:
        logger.warning(f"Query planning parsing failed: {e}. Falling back to generic queries.")
        return [
            f"{user_query} comparison 2026",
            f"{user_query} latest trends",
            f"{user_query} limitations and alternatives"
        ]
