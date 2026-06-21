from pydantic import BaseModel
from typing import Optional

class DecisionRequest(BaseModel):
    query: str
    manual_context: Optional[str] = None
    workspace_path: str

class DecisionBrief(BaseModel):
    options_considered: list[str]
    final_recommendation: str
    reasoning_summary: str
    angle_breakdown: dict[str, str]
    tradeoffs: list[str]

class DecisionResponse(BaseModel):
    brief: DecisionBrief
