# safety.py — Safety checks delegated to the LLM via system prompt.
#
# Rationale: Regex keyword lists are brittle — they block legitimate words
# (e.g. "poor" in "poor response time") and are trivially bypassed with typos.
# The Groq system prompt already instructs the model to decline vulgar, abusive,
# and out-of-scope messages. These stubs are kept so callers don't break.

def is_vulgar(text: str) -> bool:
    """Safety is handled by the LLM system prompt. Always returns False."""
    return False

def is_negative(text: str) -> bool:
    """Safety is handled by the LLM system prompt. Always returns False."""
    return False
