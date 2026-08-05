from chatbot.data import REDIRECT_BLOCK, SUPPORT_CONTACT

REPLIES = {
    "vulgar": "I am programmed to be a polite and professional assistant. Please refrain from using inappropriate language, and let me know how I can help you with questions related to ExpenseTracker.",
    
    "negative": f"We are committed to delivering the best experience with the ExpenseTracker app. If you have any concerns or specific feedback, please reach out to us directly:\n\n* ✉️ **Email:** {SUPPORT_CONTACT['email']}",
    
    "yoga": REDIRECT_BLOCK,
    
    "pricing_salary": f"For details regarding pricing, subscription hosting costs, or other queries, please contact our support team directly:\n\n* ✉️ **Email:** {SUPPORT_CONTACT['email']}",
    
    "salary": f"For details regarding such queries, please contact our team directly:\n\n* ✉️ **Email:** {SUPPORT_CONTACT['email']}",
    
    "working_hours": f"For details regarding our support availability or office timings, please contact our team directly:\n\n* ✉️ **Email:** {SUPPORT_CONTACT['email']}",
    
    "bot_identity": REDIRECT_BLOCK,
    
    "hijack": REDIRECT_BLOCK
}

