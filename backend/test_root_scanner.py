import json
from app.context.project_scanner import detect_project_context
import sys
import os

sys.path.append(os.path.abspath("."))

if __name__ == "__main__":
    context = detect_project_context("..")
    print("--- Detected Context for ROOT (..) ---")
    print(json.dumps(context, indent=2))
