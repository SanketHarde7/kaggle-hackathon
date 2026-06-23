import asyncio
import httpx
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession

async def main():
    invalid_key = "tvly-INVALID_KEY_12345"
    url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={invalid_key}"
    
    print("Testing SDK with invalid key...")
    try:
        async with streamablehttp_client(url=url) as (read_stream, write_stream, _):
            print("Connected! Initializing session...")
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("Session initialized! Calling tool...")
                result = await session.call_tool(
                    "tavily_search",
                    arguments={"query": "test", "max_results": 1, "search_depth": "advanced"},
                )
                print(f"Tool call result: {result}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
