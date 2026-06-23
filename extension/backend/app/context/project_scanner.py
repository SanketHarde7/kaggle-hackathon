import os
import json
from pathlib import Path

def detect_project_context(workspace_path: str) -> dict:
    """Reads project files to auto-detect context (dependencies, file structure)."""
    context = {
        "languages_detected": [],
        "package_manager_files_found": [],
        "key_dependencies": [],
        "file_structure_summary": "",
        "sibling_projects_detected": [],
        "detection_notes": ""
    }
    
    ws_path = Path(workspace_path)
    if not ws_path.exists() or not ws_path.is_dir():
        context["detection_notes"] = f"Workspace path '{workspace_path}' does not exist or is not a directory."
        return context
        
    # 1. Package Managers and Dependencies
    # Check for package.json
    pkg_json_path = ws_path / "package.json"
    if pkg_json_path.exists():
        context["package_manager_files_found"].append("package.json")
        if "javascript" not in context["languages_detected"]:
            context["languages_detected"].extend(["javascript", "typescript"])
        try:
            with open(pkg_json_path, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
                deps = list(pkg_data.get("dependencies", {}).keys())
                dev_deps = list(pkg_data.get("devDependencies", {}).keys())
                context["key_dependencies"].extend(deps + dev_deps)
        except Exception as e:
            context["detection_notes"] += f"Error reading package.json: {e}. "
            
    # Check for Python requirements
    req_txt_path = ws_path / "requirements.txt"
    pyproject_path = ws_path / "pyproject.toml"
    
    if pyproject_path.exists():
        context["package_manager_files_found"].append("pyproject.toml")
        if "python" not in context["languages_detected"]:
            context["languages_detected"].append("python")
        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Extremely naive pyproject parsing for common deps
                for line in content.splitlines():
                    if "=" in line and ("fastapi" in line or "flask" in line or "django" in line or "pydantic" in line or "pytest" in line):
                        dep = line.split("=")[0].strip()
                        if dep and not dep.startswith("[") and not dep.startswith("#"):
                            context["key_dependencies"].append(dep)
        except Exception as e:
            context["detection_notes"] += f"Error reading pyproject.toml: {e}. "
    elif req_txt_path.exists():
        context["package_manager_files_found"].append("requirements.txt")
        if "python" not in context["languages_detected"]:
            context["languages_detected"].append("python")
        try:
            with open(req_txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # remove version specifiers (==, >=, etc)
                        dep = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
                        context["key_dependencies"].append(dep)
        except Exception as e:
            context["detection_notes"] += f"Error reading requirements.txt: {e}. "

    # De-duplicate dependencies
    context["key_dependencies"] = list(set(context["key_dependencies"]))
            
    # 2. Shallow file structure & Sibling project scan
    ignore_dirs = {".git", "node_modules", "__pycache__", "venv", "env", ".venv", ".stackdecide"}
    try:
        top_level_items = []
        sibling_projects = []
        for item in os.scandir(ws_path):
            if item.is_dir() and item.name not in ignore_dirs:
                try:
                    # Count files in this directory (1 level deep)
                    file_count = sum(1 for subitem in os.scandir(item.path) if subitem.is_file())
                    top_level_items.append(f"{item.name}/ ({file_count} files)")
                    
                    # Check if this subdirectory is a distinct project (has its own manifest)
                    has_manifest = False
                    for manifest in ["package.json", "requirements.txt", "pyproject.toml"]:
                        if (Path(item.path) / manifest).exists():
                            has_manifest = True
                            break
                    if has_manifest:
                        sibling_projects.append(f"{item.name}/")
                        
                except PermissionError:
                    top_level_items.append(f"{item.name}/ (permission denied)")
            elif item.is_file():
                top_level_items.append(item.name)
                
        context["file_structure_summary"] = ", ".join(sorted(top_level_items))
        if len(sibling_projects) > 1:
            context["sibling_projects_detected"] = sorted(sibling_projects)
            
    except Exception as e:
        context["detection_notes"] += f"Error scanning directory structure: {e}. "
        
    return context
