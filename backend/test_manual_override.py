import json
from app.context.project_scanner import detect_project_context

if __name__ == "__main__":
    workspace_path = "."
    manual_context = "Actually, ignore the python backend, I'm building a Vue.js frontend now."
    
    project_context = detect_project_context(workspace_path)
    
    # Logic identical to routes/decision.py
    if manual_context:
        project_context["manual_context"] = manual_context
        project_context["context_override_note"] = "User provided manual context which MUST take precedence over detected auto-context if there are conflicts."
    
    project_context["workspace_path"] = workspace_path
    
    print("--- Merged Context ---")
    print(json.dumps(project_context, indent=2))
