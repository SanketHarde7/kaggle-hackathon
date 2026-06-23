from pydantic import BaseModel
from typing import Optional, Dict, List

class DecisionRequest(BaseModel):
    query: str
    manual_context: Optional[str] = None
    workspace_path: str
    proceed_anyway: bool = False  # Used to confirm continuation past the 10-decision guard

class OptionScore(BaseModel):
    option_name: str
    performance: int        # 0-10
    maintainability: int    # 0-10
    cost: int               # 0-10
    project_fit: int        # 0-10
    total_score: int        # sum of the 4 dimensions (0-40 scale)
    why_chosen_over_others: str  # 1-2 sentences focused on comparative advantage

class DecisionResult(BaseModel):
    decision_topic: str                    # e.g. "state management"
    options_considered: List[str]
    scores: List[OptionScore]
    final_pick: Optional[str] = None       # None if mismatch_warning is set
    mismatch_warning: Optional[str] = None

class DecisionBrief(BaseModel):
    """Top-level response — wraps one or more decision results."""
    original_query: str
    results: List[DecisionResult]
    annotated_prompt: str  # Call 3 output — pre-generated pure template, no LLM

class DecisionResponse(BaseModel):
    brief: DecisionBrief

class ApprovalRequiredResponse(BaseModel):
    """Returned when more than 10 decisions are detected; user must confirm to proceed."""
    requires_approval: bool = True
    decision_count: int
    decisions: List[str]

class ExtractionResult(BaseModel):
    decisions: List[str]                       # e.g. ["state management", "database"]
    queries: Dict[str, List[str]]              # exactly 2 entries per decision key
    mismatch_warnings: Dict[str, str]          # decision -> warning text; only for mismatched decisions
