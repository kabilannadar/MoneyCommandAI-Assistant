from chatbot.data import (
    EXPENSE_TRACKER_INFO,
    DEFAULT_CATEGORIES,
    SUPPORTED_PAYMENT_METHODS,
    V1_FEATURES,
    V2_FEATURES,
    TELEGRAM_SETUP_GUIDE,
    TELEGRAM_LOGGING_SYNTAX,
    SUPPORT_CONTACT,
)

def _greeting_block():
    return "\n\n## Greeting Instruction\n- Greet the user warmly, politely, and professionally. Offer assistance regarding ExpenseTracker features, dashboard guide, or Telegram bot setup details.\n"

def _telegram_setup_block():
    return f"""\n\n## Telegram Bot Connection Setup Guide
{TELEGRAM_SETUP_GUIDE}
"""

def _telegram_logging_block():
    return f"""\n\n## Telegram Message Parsing Rules & Syntaxes
{TELEGRAM_LOGGING_SYNTAX}
- Default Categories: {DEFAULT_CATEGORIES}
- Supported Payment Methods: {SUPPORTED_PAYMENT_METHODS}
"""

def _app_features_block():
    v1_str = "\n".join([f"- {f}" for f in V1_FEATURES])
    v2_str = "\n".join([f"- {f}" for f in V2_FEATURES])
    return f"""\n\n## ExpenseTracker Application Features
**V1 (Core Features):**
{v1_str}

**V2 (Extended Features):**
{v2_str}
"""

def _support_contact_block():
    return f"""\n\n## Customer Support Contact Details
- ✉️ Email: [{SUPPORT_CONTACT["email"]}](mailto:{SUPPORT_CONTACT["email"]})
- 🤖 Telegram Bot: [{SUPPORT_CONTACT["bot_handle"]}](https://t.me/expensetrackertnbot)
"""

def _decline_block(focus_name: str, selected_redirect: str) -> str:
    email = f"[{SUPPORT_CONTACT['email']}](mailto:{SUPPORT_CONTACT['email']})"
    bot = f"[{SUPPORT_CONTACT['bot_handle']}](https://t.me/expensetrackertnbot)"
    return f"""
## What to Decline
**CRITICAL:** You are NOT a general-purpose AI. You are ONLY allowed to discuss the ExpenseTracker application. Do NOT answer questions about general knowledge, history, geography, science, other brands, or any topic unrelated to ExpenseTracker. If the query is not directly about ExpenseTracker's features, dashboard, spreadsheet exports, or Telegram bot setup/logging, you MUST politely decline and state that it is outside your scope. *(Exception: Short follow-up queries like "and", "more", "what else", "next" are valid continuations of the conversation; you must NOT decline them).*

**CONDITIONAL REDIRECT RULE:**
IF AND ONLY IF the user's query is completely off-topic and you are declining it, you must format your response using this structure:
1. Write a single, brief sentence politely stating that you cannot answer the query because you only support the ExpenseTracker app. Do not copy the wording of this instruction.
2. Write a single short transition sentence introducing ExpenseTracker features. Do not copy the wording of this instruction.
3. List the following highlights about ExpenseTracker's {focus_name} (each on its own new line):
{selected_redirect}
4. List the following contact details (each on its own new line):
   - 🤖 Telegram Bot: {bot}
   - ✉️ Email: {email}

**CRITICAL:**
- Do NOT use the above 1-4 redirect structure for greetings, setup setup queries, or any other query that is within scope.
- Every bullet point and contact detail line must be on its own new line.
"""

def _live_support_offline_block(enable_live_support: bool = True) -> str:
    if not enable_live_support:
        return """\n\n## CRITICAL: Live Chat Support is unavailable
- Connecting to a live human support agent is currently offline and unavailable.
- If the user explicitly asks to connect to a live support agent, chat with a human, or start a live support session, politely inform them that live chat support is currently offline, and offer to help them directly here instead.
"""
    return ""
