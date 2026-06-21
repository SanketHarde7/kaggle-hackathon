import re

def _clean_snippet(text: str) -> str:
    """Strip markdown formatting artifacts, table syntax, and common scraping noise."""
    # Remove markdown bold/italic markers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    # Remove markdown heading markers
    text = re.sub(r'^#{1,6}\s+', '', text)
    # Remove table syntax: rows of pipes/dashes like |---|---|
    text = re.sub(r'\|[\s\-:]+\|', ' ', text)
    # Remove remaining pipe characters used as column separators
    text = re.sub(r'\s*\|\s*', ' ', text)
    # Remove excessive dash/equal sequences (--- or ===)
    text = re.sub(r'[-=]{3,}', '', text)
    # Remove markdown link syntax, keep the text: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove markdown image syntax: ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Remove inline code backticks but keep the content
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove bullet point markers at start of lines
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text)
    # Collapse newlines into spaces
    text = text.replace("\n", " ").strip()
    # Collapse multiple spaces
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def clean_results(raw_results: list[dict]) -> str:
    seen_urls = set()
    grouped_results = {}
    
    for item in raw_results:
        url = item.get("url")
        query = item.get("query", "General Search")
        snippet = item.get("snippet", "")
        
        if not url or url in seen_urls or not snippet:
            continue
            
        seen_urls.add(url)
        snippet = _clean_snippet(snippet)
        
        if not snippet:
            continue
            
        if query not in grouped_results:
            grouped_results[query] = []
            
        grouped_results[query].append(f"- [Source: {url}] {snippet}")
        
    output_lines = []
    for query, lines in grouped_results.items():
        output_lines.append(f"## Query: \"{query}\"")
        output_lines.extend(lines)
        output_lines.append("")
        
    return "\n".join(output_lines)
