from pydantic import BaseModel
from typing import Optional, Dict

class DecisionRequest(BaseModel):
    query: str
    manual_context: Optional[str] = None
    workspace_path: str

class DecisionBrief(BaseModel):
    options_considered: list[str]
    final_recommendation: str
    reasoning_summary: str
    context_mismatch_warning: Optional[str] = None
    angle_breakdown: Dict[str, str]
    tradeoffs: list[str]

class DecisionResponse(BaseModel):
    brief: DecisionBrief
