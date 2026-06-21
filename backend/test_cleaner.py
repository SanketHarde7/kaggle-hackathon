import re

# Old cleaner (from Prompt #3)
def old_clean(snippet):
    snippet = snippet.replace("\n", " ").strip()
    while "  " in snippet:
        snippet = snippet.replace("  ", " ")
    return snippet

# New cleaner
def new_clean(text):
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text)
    text = re.sub(r'\|[\s\-:]+\|', ' ', text)
    text = re.sub(r'\s*\|\s*', ' ', text)
    text = re.sub(r'[-=]{3,}', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text)
    text = text.replace("\n", " ").strip()
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

sample = """# Redux vs Zustand: Choosing the Right React State Manager. **TL;DR:** Choosing a state manager can make or break your React architecture. | **What matters for shipping** | **Redux Toolkit + React-Redux** | **Zustand** |. * **The hybrid approach** combines RTK Query's server state management with Zustand's lightweight UI state handling, which is increasingly popular for complex applications requiring both structure and performance."""

print("=== BEFORE (old cleaner) ===")
print(old_clean(sample))
print()
print("=== AFTER (new cleaner) ===")
print(new_clean(sample))
