from chatbot.data import REDIRECT_BLOCK, SUPPORT_CONTACT

REPLIES = {
    # Politely decline vulgar/abusive input (safety fallback — LLM handles this normally)
    "vulgar": "I'm here to keep things professional and helpful! Please keep the conversation respectful, and I'll be happy to assist with any ExpenseTracker or MoneyCommandAI features you need.",

    # Empathetically respond to negative feedback (LLM handles this normally)
    "negative": f"We're truly sorry to hear about your experience — your feedback matters a lot to us. Please reach out to our support team directly so we can make things right:\n\n* 💬 **Support & Feedback Page:** [Support & Feedback](https://expensetrackertn.vercel.app/support) (Most Recommended)\n* ✉️ **Email:** [{SUPPORT_CONTACT['email']}](mailto:{SUPPORT_CONTACT['email']})",
}
