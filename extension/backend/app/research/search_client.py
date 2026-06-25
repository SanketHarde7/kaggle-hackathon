"""
Tavily search via MCP (Model Context Protocol) over Streamable HTTP using the official Python SDK.
"""

import json
import logging
import asyncio
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from app.config import get_active_tavily_key

logger = logging.getLogger(__name__)

class SearchProviderError(Exception):
    """Exception raised for general search provider failures or timeouts."""
    pass

class SearchProviderAuthError(Exception):
    """Exception raised when the Tavily API key is missing or invalid."""
    pass

async def search(query: str, max_results: int = 5) -> list[dict]:
    """
    Executes a web search query using the Tavily MCP endpoint.

    Args:
        query (str): The search term or query string.
        max_results (int, optional): The maximum number of results to fetch. Defaults to 5.

    Returns:
        list[dict]: A list of dictionaries, where each dict represents a search result
            containing 'title', 'snippet', and 'url' keys.

    Raises:
        SearchProviderAuthError: If the Tavily API key is invalid or unauthorized.
        SearchProviderError: If the search request fails, times out, or returns invalid data.
    """
    tavily_key = get_active_tavily_key()
    if not tavily_key:
        raise SearchProviderError("Tavily API key is not configured.")

    server_url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_key}"

    try:
        async with asyncio.timeout(10.0):
            async with streamablehttp_client(url=server_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    result = await session.call_tool(
                        "tavily_search",
                        arguments={
                            "query": query,
                            "max_results": max_results,
                            "search_depth": "advanced",
                        },
                    )

                    # Check isError flag
                    if getattr(result, "isError", False):
                        error_text = ""
                        for cb in getattr(result, "content", []):
                            if getattr(cb, "type", "") == "text":
                                error_text += getattr(cb, "text", "")
                        if "unauthorized" in error_text.lower() or "invalid" in error_text.lower() or "missing" in error_text.lower():
                            raise SearchProviderAuthError("Your Tavily API key appears to be invalid.")
                        raise SearchProviderError(f"Tavily MCP tool error: {error_text}")

                    # Extract search results from content blocks
                    results = []
                    for content_block in getattr(result, "content", []):
                        if getattr(content_block, "type", "") != "text":
                            continue
                        
                        text_val = getattr(content_block, "text", "")
                        try:
                            data = json.loads(text_val)
                        except (json.JSONDecodeError, KeyError, TypeError):
                            logger.warning(f"Non-JSON text from Tavily MCP: {text_val[:200]}")
                            continue

                        # Check for embedded error responses (Tavily returns these inside content text)
                        if isinstance(data, dict) and "error" in data:
                            status = data.get("status", 0)
                            detail = data.get("detail", {})
                            err_msg = detail.get("error", data["error"]) if isinstance(detail, dict) else str(detail or data["error"])
                            if status in (401, 403) or "unauthorized" in err_msg.lower() or "invalid" in err_msg.lower() or "missing" in err_msg.lower():
                                raise SearchProviderAuthError("Your Tavily API key appears to be invalid.")
                            raise SearchProviderError(f"Tavily search error: {err_msg}")

                        # Handle both list-of-results and wrapped {"results": [...]} shapes
                        raw_results = []
                        if isinstance(data, list):
                            raw_results = data
                        elif isinstance(data, dict) and "results" in data:
                            raw_results = data["results"]
                        elif isinstance(data, dict):
                            raw_results = [data]

                        for r in raw_results:
                            results.append({
                                "title": r.get("title", ""),
                                "snippet": r.get("content", r.get("snippet", "")),
                                "url": r.get("url", ""),
                            })

                    return results

    except SearchProviderAuthError:
        raise
    except SearchProviderError:
        raise
    except asyncio.TimeoutError:
        raise SearchProviderError("Search timed out after 10 seconds.")
    except Exception as e:
        # In Python 3.11+, anyio TaskGroups wrap exceptions in ExceptionGroup/BaseExceptionGroup.
        # These can be nested if there are multiple context managers.
        def find_exception(exc, target_type):
            if isinstance(exc, target_type):
                return exc
            if isinstance(exc, BaseExceptionGroup):
                for sub in exc.exceptions:
                    res = find_exception(sub, target_type)
                    if res: return res
            return None

        auth_err = find_exception(e, SearchProviderAuthError)
        if auth_err:
            raise auth_err
        
        provider_err = find_exception(e, SearchProviderError)
        if provider_err:
            raise provider_err

        # Security: sanitize error message to ensure the API key is never leaked in tracebacks
        err_str = str(e)
        if tavily_key and tavily_key in err_str:
            err_str = err_str.replace(tavily_key, "HIDDEN_API_KEY")
            
        raise SearchProviderError(f"Search failed: {err_str}")
