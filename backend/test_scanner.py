import json
from app.context.project_scanner import detect_project_context

if __name__ == "__main__":
    context = detect_project_context(".")
    print("--- Detected Context for backend/ ---")
    print(json.dumps(context, indent=2))
