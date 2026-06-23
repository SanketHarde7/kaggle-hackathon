import re
from app.memory.store import load_memory

def _approximate_tokens(text: str) -> int:
    return len(text) // 4

def _is_related(query1: str, query2: str) -> bool:
    """Simple heuristic to check if two queries are related based on word overlap."""
    stop_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "about", "how", "what", "why", "when", "where", "is", "are", "do", "does", "did", "should", "i", "you", "we", "they", "it", "this", "that"}
    
    words1 = set(re.findall(r'\b\w+\b', query1.lower())) - stop_words
    words2 = set(re.findall(r'\b\w+\b', query2.lower())) - stop_words
    
    return bool(words1 & words2)

def build_memory_context(workspace_path: str, current_query: str, token_budget: int = 1500) -> str:
    """Builds a context string from past decisions, prioritizing related ones."""
    memory_data = load_memory(workspace_path)
    decisions = memory_data.get("decisions", [])
    
    if not decisions:
        return ""
        
    # Categorize decisions into related and unrelated
    related_decisions = []
    unrelated_decisions = []
    
    # We process in reverse chronological order (newest first)
    for dec in reversed(decisions):
        if _is_related(dec["query"], current_query):
            related_decisions.append(dec)
        else:
            unrelated_decisions.append(dec)
            
    # Combine lists, related first
    prioritized_decisions = related_decisions + unrelated_decisions
    
    context_lines = ["## Past decisions in this project:"]
    current_tokens = _approximate_tokens(context_lines[0])
    
    for dec in prioritized_decisions:
        is_related = dec in related_decisions
        prefix = "- [related] " if is_related else "- "
        
        # Build the line(s) for this decision
        if is_related:
            # 2-3 lines of detail
            tradeoffs = ""
            # Some old decisions might not have tradeoffs explicitly saved as lists, but we can extract angle_breakdown or just use reasoning summary.
            # The prompt asks for "query -> final_recommendation (one-line reasoning)" and a slightly more detailed version if related.
            line1 = f"{prefix}{dec['query']} -> {dec['final_recommendation']}"
            line2 = f"  Reasoning: {dec['reasoning_summary']}"
            entry = f"{line1}\n{line2}"
        else:
            # 1 line of detail
            entry = f"{prefix}{dec['query']} -> {dec['final_recommendation']} ({dec['reasoning_summary']})"
            
        entry_tokens = _approximate_tokens(entry)
        
        if current_tokens + entry_tokens > token_budget:
            break
            
        context_lines.append(entry)
        current_tokens += entry_tokens
        
    if len(context_lines) == 1: # Only the header was added
        return ""
        
    return "\n".join(context_lines)
