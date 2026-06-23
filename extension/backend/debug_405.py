import asyncio
import httpx
from app.config import get_active_tavily_key

async def main():
    valid_key = get_active_tavily_key()
    invalid_key = "tvly-INVALID_KEY_12345"
    
    urls = {
        "VALID_KEY": f"https://mcp.tavily.com/mcp/?tavilyApiKey={valid_key}",
        "INVALID_KEY": f"https://mcp.tavily.com/mcp/?tavilyApiKey={invalid_key}"
    }
    
    async with httpx.AsyncClient() as client:
        for key_type, url in urls.items():
            print(f"\n{'='*40}\nTesting GET with {key_type}\n{'='*40}")
            try:
                # streamablehttp_client makes a GET request first with Accept: text/event-stream
                headers = {"Accept": "text/event-stream"}
                resp = await client.get(url, headers=headers)
                print(f"Status Code: {resp.status_code}")
                print(f"Headers: {dict(resp.headers)}")
                print(f"Body: {resp.text[:500]}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
