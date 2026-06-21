import json
import os
from pathlib import Path
import logging

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
