import asyncio
import json
import sys
import os

sys.path.append(os.path.abspath("."))
from app.routes.decision import analyze_decision_route
from app.models.schemas import DecisionRequest

async def test():
    req1 = DecisionRequest(
        query="Should I use Zustand or Redux for state management?",
        workspace_path="."
    )
    req2 = DecisionRequest(
        query="Should I use SQLite or Postgres for this project?",
        workspace_path="."
    )
    
    # print("=== TEST 1: Mismatched Query (Zustand/Redux vs Backend) ===")
    # res1 = await analyze_decision_route(req1)
    # print(json.dumps(res1.model_dump(), indent=2))
    
    print("\n=== TEST 2: Matched Query (SQLite/Postgres vs Backend) ===")
    res2 = await analyze_decision_route(req2)
    print(json.dumps(res2.model_dump(), indent=2))

if __name__ == "__main__":
    asyncio.run(test())
