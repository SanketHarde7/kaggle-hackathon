import httpx
from app.config import settings

class SearchProviderError(Exception):
    pass

async def search(query: str, max_results: int = 5) -> list[dict]:
    if not settings.tavily_api_key:
        raise SearchProviderError("Tavily API key is not configured.")
        
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_images": False,
        "include_raw_content": False,
        "max_results": max_results,
        "include_domains": [],
        "exclude_domains": []
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for result in data.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("content", ""),
                    "url": result.get("url", "")
                })
            return results
    except Exception as e:
        raise SearchProviderError(f"Search failed: {e}")
