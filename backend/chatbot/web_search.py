"""
web_search.py - DuckDuckGo web search fallback for the ExpenseTracker Assistant.
Called ONLY when the local RAG knowledge base doesn't have relevant information
AND the query is within the scope defined by the system prompt.

Allowed scope (mirrors the system prompt):
  - Personal finance, logging transactions, expense tracker
  - Telegram bot, Telegram webhooks, linking account via chat ID
  - App features: dashboard, budgets, goals, reminders, subscriptions, EMIs
  - Data export (CSV, Excel)
"""

import re


def search_web(query: str, max_results: int = 4) -> str:
    """
    Search the web using DuckDuckGo and return a concise context string.
    Returns an empty string if the search fails or returns no results.
    """
    try:
        from ddgs import DDGS

        snippets = []
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")
            
            if body:
                snippets.append(f"Source: {title} ({href})\nContent: {body}")

        if snippets:
            context = "\n\n".join(snippets)
            print(f"[WEB SEARCH] Query: '{query}' | Found {len(snippets)} results")
            return context

    except Exception as e:
        print(f"[WEB SEARCH ERROR] {str(e)}")

    return ""


# ---------------------------------------------------------------------------
# Topics that are within scope of the ExpenseTracker Assistant system prompt.
# Web search is ONLY triggered if the query matches at least one of these.
# ---------------------------------------------------------------------------
_ALLOWED_TOPIC_KEYWORDS = {
    # App functionality & settings
    "expense", "income", "budget", "category", "recurring", "goal",
    "subscription", "emi", "debt", "loan", "reminder", "setup",
    "dashboard", "visual", "graph", "chart", "pie chart", "area chart",
    "audit log", "profile", "export", "csv", "excel",
    "currency", "timezone", "dark mode", "light mode",

    # Telegram bot connection
    "telegram", "bot", "webhook", "chat id", "chat_id", "link account",
    "connect account", "pair bot", "telegram setup", "telegram command",
}


def should_use_web_search(message: str, has_rag_context: bool) -> bool:
    """
    Decide whether to fall back to web search.

    Returns True ONLY when ALL of the following are true:
      1. RAG found no relevant context
      2. The query is NOT a greeting / chitchat
      3. The query is NOT an explicitly restricted topic
      4. The query IS related to at least one allowed topic in the system prompt scope
    """
    # 1. If RAG already has context, no web search needed
    if has_rag_context:
        return False

    q = message.strip().lower()

    # 2. Skip pure greetings / chitchat
    non_search_patterns = [
        r"^(hi|hello|hey|bye|thanks|thank you|good morning|good afternoon|good evening)[\s!?.,]*$",
        r"^(how are you|who are you|what is your name|tell me about yourself)[\s!?.,]*$",
    ]
    for pat in non_search_patterns:
        if re.match(pat, q):
            return False

    # 3. Hard-blocked topics (never search these)
    restricted_keywords = {
        "medical", "doctor", "hospital", "disease", "medicine", "drug",
        "legal", "lawyer", "court", "lawsuit", "attorney",
        "election", "politician", "government policy",
        "cricket score", "football score", "sports score",
        "movie review", "film review", "celebrity gossip",
        "homework", "exam answer", "cheat",
        "recipe", "cooking", "restaurant",
        "weather", "forecast", "climate",
        "news", "headline", "breaking news",
    }
    for kw in restricted_keywords:
        if kw in q:
            print(f"[WEB SEARCH BLOCKED] Restricted topic detected: '{kw}' in query: '{message}'")
            return False

    # 4. MUST match at least one allowed topic keyword
    for kw in _ALLOWED_TOPIC_KEYWORDS:
        if kw in q:
            print(f"[WEB SEARCH ALLOWED] Matched topic keyword: '{kw}' in query: '{message}'")
            return True

    # Query doesn't match any allowed topic — skip web search
    print(f"[WEB SEARCH SKIPPED] No allowed topic matched for query: '{message}'")
    return False

