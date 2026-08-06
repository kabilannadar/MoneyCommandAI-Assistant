import re

def detect_intent(question, has_context=False):
    q_clean = question.strip().lower().rstrip("?!.")
    
    # 1. Greetings and basic chitchat
    greetings = {
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening", 
        "how are you", "who are you", "what is your name", "help", "greet", "greetings",
        "thank you", "thanks", "bye", "goodbye", "see you"
    }
    if q_clean in greetings or any(q_clean.startswith(g + " ") for g in greetings):
        return "GREETING"

    # 2. Telegram Bot Setup Setup / Connection Setup
    setup_keywords = {
        "connect", "link", "chat id", "chat_id", "telegram setup", "setup telegram", 
        "integrate telegram", "link telegram", "connect telegram", "telegram bot", 
        "telegram account", "register bot", "pair bot"
    }
    if any(k in q_clean for k in setup_keywords):
        return "TELEGRAM_SETUP"

    # 3. Telegram Message Formatting / Logging commands
    logging_keywords = {
        "how to log", "logging", "format", "command", "syntax", "example", 
        "log expense", "log income", "log recurring", "log emi", "log debt", 
        "log goal", "log subscription", "log category", "log budget", "log reminder",
        "how do i add", "add expense", "add income", "add category"
    }
    if any(k in q_clean for k in logging_keywords):
        return "TELEGRAM_LOGGING"

    # 4. MoneyCommandAI general application features / capabilities
    feature_keywords = {
        "feature", "capability", "dashboard", "chart", "pie chart", "area chart",
        "budget", "income", "reminder", "goal", "recurring", "subscription", 
        "audit log", "profile", "export", "csv", "excel", "sheet", 
        "currency", "dark mode"
    }
    if any(k in q_clean for k in feature_keywords):
        return "APP_FEATURES"

    # 5. Support / Contact details
    support_keywords = {
        "contact", "support", "email", "reach out", "help desk", "support team", 
        "human", "live chat", "offline", "agent", "talk to"
    }
    if any(k in q_clean for k in support_keywords):
        return "SUPPORT_CONTACT"

    # 6. Fallback based on context presence
    if has_context:
        return "APP_FEATURES"
        
    # 7. Default fallback
    return "GENERAL_KNOWLEDGE"


