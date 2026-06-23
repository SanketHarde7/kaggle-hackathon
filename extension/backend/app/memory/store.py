import json
import os
from pathlib import Path
import logging
from datetime import datetime, timezone
from app.models.schemas import DecisionResult

logger = logging.getLogger(__name__)


def load_memory(workspace_path: str) -> dict:
    memory_file = Path(workspace_path) / ".stackdecide" / "memory.json"

    if not memory_file.exists():
        return {"decisions": []}

    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode memory.json in {workspace_path}: {e}. Returning empty memory.")
        return {"decisions": []}
    except Exception as e:
        logger.error(f"Unexpected error reading memory.json in {workspace_path}: {e}. Returning empty memory.")
        return {"decisions": []}


def save_memory(workspace_path: str, data: dict) -> None:
    stackdecide_dir = Path(workspace_path) / ".stackdecide"
    memory_file = stackdecide_dir / "memory.json"

    try:
        stackdecide_dir.mkdir(parents=True, exist_ok=True)
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save memory.json in {workspace_path}: {e}")


def add_decision(workspace_path: str, result: DecisionResult) -> dict:
    """
    Appends one record per DecisionResult topic to memory.json.
    One record per *decision topic* so context_builder's relatedness matching
    still works at the right granularity (topic-level, not whole-request-level).
    """
    memory_data = load_memory(workspace_path)
    decisions = memory_data.get("decisions", [])

    new_id = f"dec_{len(decisions) + 1:03d}"

    # Store the best option's reasoning for context_builder readability
    final_pick = result.final_pick
    best_score_obj = next(
        (s for s in result.scores if s.option_name == final_pick), None
    ) if result.scores else None

    decision_record = {
        "id": new_id,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "query": result.decision_topic,   # topic used as the query key for relatedness matching
        "decision_topic": result.decision_topic,
        "final_pick": final_pick,
        "mismatch_warning": result.mismatch_warning,
        "options_considered": result.options_considered,
        "scores_summary": [
            {
                "option": s.option_name,
                "total_score": s.total_score,
                "why": s.why_chosen_over_others,
            }
            for s in result.scores
        ],
        # Legacy fields kept so old context_builder code still works
        "final_recommendation": final_pick or f"(mismatch) {result.mismatch_warning}",
        "reasoning_summary": (
            best_score_obj.why_chosen_over_others
            if best_score_obj
            else (result.mismatch_warning or "")
        ),
    }

    decisions.append(decision_record)
    memory_data["decisions"] = decisions
    save_memory(workspace_path, memory_data)

    return decision_record
