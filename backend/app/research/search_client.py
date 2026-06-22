import httpx
from app.config import get_active_tavily_key

class SearchProviderError(Exception):
    pass

class SearchProviderAuthError(Exception):
    pass

async def search(query: str, max_results: int = 5) -> list[dict]:
    tavily_key = get_active_tavily_key()
    if not tavily_key:
        raise SearchProviderError("Tavily API key is not configured.")
        
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": tavily_key,
        "query": query,
        "search_depth": "advanced",
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
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            raise SearchProviderAuthError("Your Tavily API key appears to be invalid.")
        raise SearchProviderError(f"Search failed with status: {e.response.status_code}")
    except Exception as e:
        raise SearchProviderError(f"Search failed: {e}")
