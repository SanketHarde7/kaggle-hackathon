import asyncio
from app.providers.base import LLMProvider
from app.research.query_planner import plan_queries
from app.research.search_client import search
from app.research.cleaner import clean_results

async def run_research(user_query: str, project_context: dict, provider: LLMProvider) -> str:
    queries = await plan_queries(user_query, project_context, provider)
    
    async def search_with_query(q: str):
        try:
            results = await search(q)
            for r in results:
                r["query"] = q
            return results
        except Exception:
            return []
            
    tasks = [search_with_query(q) for q in queries]
    search_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_results = []
    success_count = 0
    for res in search_results:
        if isinstance(res, list) and res:
            all_results.extend(res)
            success_count += 1
            
    if success_count == 0 and len(queries) > 0:
        raise Exception("All search queries failed.")
        
    return clean_results(all_results)
