# data.py — Central knowledge base & metadata for the ExpenseTracker application.

EXPENSE_TRACKER_INFO = {
    "name": "MoneyCommandAI",
    "description": "A full-stack personal finance tracker built with FastAPI (backend) and React/Vite (frontend) that allows users to manage expenses, incomes, budgets, recurring transactions, goals, and reminders.",
    "tech_stack": {
        "frontend": "React 18, Vite, Vanilla CSS, React Query, React Router v6, Recharts",
        "backend": "FastAPI, SQLAlchemy, JWT, Pydantic v2",
        "database": "SQLite (local development) / PostgreSQL (production deployment)"
    }
}

DEFAULT_CATEGORIES = {
    "expense": ["Food", "Transport", "Groceries", "Entertainment", "Health", "Shopping", "Utilities", "Education", "Rent"],
    "income": ["Salary", "Freelancing", "Gifts", "Other"]
}

SUPPORTED_PAYMENT_METHODS = ["upi", "cash", "card", "bank", "netbanking", "wallet", "online", "cheque"]

V1_FEATURES = [
    "JWT Authentication — Secure sign-up, login, and profile management.",
    "Categories CRUD — Custom category setup with 12 default categories pre-seeded upon registration.",
    "Expenses CRUD — Log expenses with search and filtering by category, payment method, or date.",
    "Income Tracking — Log income sources like Salary, Freelancing, Gifts, or Other.",
    "Budgets — Set global monthly/weekly budgets, as well as specific budget limits per category."
]

V2_FEATURES = [
    "Goals — Set financial targets, track total saved, and view completion progress percentage.",
    "Reminders — Schedule bill reminders with overdue status detection and quick mark-as-done actions.",
    "Recurring Transactions — Automate weekly/monthly transactions.",
    "Subscriptions — Register recurring subscriptions with active alerts when the renewal date is near.",
    "Audit Logs — View a timestamped timeline of every action (adds, edits, deletes) made in the app.",
    "User Profile — Customize currency symbol (e.g. ₹, $, €), timezone, and light/dark theme preference.",
    "Data Export — Download full spreadsheets of transactions in CSV or Excel format with date range filters."
]

TELEGRAM_SETUP_GUIDE = """
To connect this chat or any Telegram account to your MoneyCommandAI web account:
1. Open the Telegram Bot [**@expensetrackertnbot**](https://t.me/expensetrackertnbot) and send `/start`. It will print your unique numeric Chat ID (e.g., `123456789`).
2. Log into the MoneyCommandAI Web UI.
3. Navigate to **Settings → Telegram Bot Setup** page.
4. Paste your Chat ID into the input field and click **Link Telegram Account**.
5. Once linked, the bot will notify you. You can start sending transaction logs instantly!
"""

TELEGRAM_LOGGING_SYNTAX = """
Message syntax: `<type?> <title> <amount> <payment mode?> <note?>`

Supported transaction types (prefix keywords):
- Expense (Default — prefix optional): `Pizza 150 upi` or `movie 300 card for night out`
- Income: (Prefix: `income` or `inc`): `income Project 25000 bank freelancing`
- Category: (Prefix: `category` or `cat`): `category Medical #ef4444 cross`
- Budget: (Prefix: `budget`): `budget Food 5000` or `budget 30000` (global budget)
- Recurring: (Prefix: `recurring` or `recur`): `recurring Rent 15000 monthly bank`
- Goal: (Prefix: `goal` or `saving`): `goal New Laptop 95000 upi saving for work`
- Subscription: (Prefix: `sub` or `subscription`): `sub Netflix 649 card monthly`
- EMI: (Prefix: `emi`): `emi Car Loan 8500 netbanking`
- Debt: (Prefix: `debt`): `debt John 2000 cash borrowed for trip`
- Reminder: (Prefix: `remind` or `reminder`): `remind Electricity Bill 1450 tomorrow`
"""

SUPPORT_CONTACT = {
    "email": "r.r.kabilan0335@gmail.com",
    "bot_handle": "@expensetrackertnbot"
}

# Redirect blocks for off-topic queries
REDIRECT_BLOCK = f"""Outside scope, but here is MoneyCommandAI! 😊
- 🌐 Website: Visit your local dashboard [expensetrackertn.vercel.app](https://expensetrackertn.vercel.app/)
- 🤖 Telegram Bot: Link via settings using your Chat ID (Bot: [{SUPPORT_CONTACT["bot_handle"]}](https://t.me/expensetrackertnbot))
- ✉️ Support: Reach out to [{SUPPORT_CONTACT["email"]}](mailto:{SUPPORT_CONTACT["email"]})"""

REDIRECT_FEATURES = """- 📊 **Interactive Dashboard**: View visual graphs (pie/area charts) of your monthly trends and category-wise spending.
- ⏰ **Smart Utilities**: Schedule EMIs, goals, bill reminders, and subscriptions with automated renewal alerts.
- 📥 **Export Reports**: Generate Excel/CSV spreadsheets of all logged finances instantly."""

REDIRECT_TELEGRAM = """- ⚡ **Instant Logging**: Message transactions directly to Telegram like: `Coffee 80 cash`.
- 🔗 **Easy Link**: Securely connect using your Telegram Chat ID in **Settings → Telegram Bot**.
- 🛠️ **Full Command Support**: Log incomes, budgets, reminders, debts, and EMIs on-the-go."""

