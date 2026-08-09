# data.py — Central knowledge base for ExpenseTracker + MoneyCommandAI chatbot.

EXPENSE_TRACKER_INFO = {
    "name": "ExpenseTracker",
    "description": (
        "ExpenseTracker is a personal finance tracking app that helps you manage your money — "
        "track expenses and income, set budgets, save towards goals, manage loans and EMIs, "
        "stay on top of bills, and understand your spending through visual charts and reports. "
        "MoneyCommandAI is the built-in AI companion that makes ExpenseTracker smarter — it powers "
        "the Telegram bot, letting you log transactions instantly by just sending a message, and "
        "it also runs this support assistant."
    ),
    "url": "https://expensetrackertn.vercel.app",
    "tech_stack": {
        "frontend": "React 18 with Vite",
        "backend": "FastAPI (Python)",
        "database": "SQLite (dev) / PostgreSQL (production)",
    }
}

DEFAULT_CATEGORIES = {
    "expense": ["Food", "Transport", "Groceries", "Entertainment", "Health", "Shopping", "Utilities", "Education", "Rent"],
    "income": ["Salary", "Freelancing", "Gifts", "Other"]
}

SUPPORTED_PAYMENT_METHODS = ["UPI", "Cash", "Card", "Net Banking", "Wallet", "Cheque / Other"]

PAYMENT_MODES_GUIDE = """
When you log a transaction, you can choose how the money was paid or received:
- 💳 **UPI** — For payments via GPay, PhonePe, Paytm, etc. (this is the default if you don't specify one)
- 💵 **Cash** — Physical cash
- 💳 **Card** — Debit or credit card
- 🏦 **Net Banking** — Online bank transfers (NEFT, IMPS, RTGS)
- 👛 **Wallet** — Digital wallets
- 📄 **Cheque / Other** — Cheques or any other method

These are just labels to help you keep track of how you pay — the app never asks for your card number, PIN, or bank password.
"""

# ─── Feature Descriptions (user-friendly, no developer jargon) ───────────────

DASHBOARD_FEATURES = """
The **Dashboard** is your financial overview at a glance:
- See your total expenses, monthly income, and net savings on summary cards
- View a **spending streak** — how many days in a row you've logged transactions
- A **pie chart** breaks down your spending by category (Food, Transport, etc.)
- An **area chart** shows your income vs. expenses trend over the past months
- A **budget progress bar** shows how much of your monthly budget you've used
- Quick-action buttons let you take a guided tour of the app or import expenses from a CSV file
- An **announcement ticker** shows the latest app updates at the top of the screen

💡 The dashboard auto-refreshes every time you open it, so your numbers are always up to date.
"""

ONBOARDING_TOUR = """
When you open ExpenseTracker for the first time, a **guided tour** automatically starts — it walks you through every section of the app step by step. You can also re-launch it at any time by clicking the **"Take a Tour"** button on the Dashboard.
"""

EXPENSE_FEATURES = """
The **Expenses** page is where you log money going out:
- Add an expense with a title, amount, category, payment method, date, and an optional note
- Search and filter your expenses by keyword, category, payment method, or date range
- Edit or delete any expense record
- View a clean list of all your expenses, sorted by date

**Telegram shortcut:** `Coffee 80 upi` or just `Coffee 80` (UPI is the default)
"""

INCOME_FEATURES = """
The **Income** page tracks money coming in:
- Log income with a source name (Salary, Freelancing, Gifts, etc.), amount, date, and notes
- Filter income by source or date range
- Edit or delete any income record
- All income is reflected in your Dashboard savings calculation

**Telegram shortcut:** `income Freelance Project 25000 bank`
"""

CATEGORY_FEATURES = """
**Categories** help you organize your transactions:
- ExpenseTracker comes with default categories like Food, Transport, Health, Rent, Salary, etc.
- You can create your own custom categories with a name and a color
- Each category can have its own icon (chosen from a set of symbols)
- Categories are used across expenses, budgets, and the dashboard pie chart

**Telegram shortcut:** `category Medical` (or `category Medical cross` for custom icon)
"""

BUDGET_FEATURES = """
The **Budget** page helps you control your spending:
- Set a **global monthly budget** — a total spending cap for the month
- Set **category-level budgets** — e.g., limit Food spending to ₹5,000 per month
- The dashboard shows a real-time progress bar so you can see how close you are to your limit
- You'll see color-coded warnings when you're approaching or over your budget

**Telegram shortcut:** `budget Food 5000` or `budget 30000` (for global budget)
"""

SAVINGS_FEATURES = """
The **Savings** page gives you a clear picture of your saving health:
- See your **Projected Savings** — how much you should save based on income minus your budget
- See your **Actual Savings** — income minus what you actually spent
- Log savings manually (deposits or withdrawals) to build a savings history
- A health indicator tells you if your savings rate is Excellent, Good, Average, or Unsatisfactory
- Income is broken down by source with percentage contribution
"""

GOALS_FEATURES = """
The **Goals** page helps you save towards specific targets:
- Create a goal with a name and a target amount (e.g., "New Laptop — ₹95,000")
- Log savings against the goal to track your progress
- A progress bar shows how close you are to your target
- You can have multiple goals running at the same time

**Telegram shortcut:** `goal New Laptop 95000`
"""

REMINDERS_FEATURES = """
**Reminders** keep you from missing important payments:
- Set a reminder for any upcoming bill or payment with a title, amount, and due date
- Overdue reminders are highlighted so you can spot them immediately
- Edit or delete reminders as needed
- Reminders appear on your dashboard if they're coming up soon

**Telegram shortcut:** `remind Electricity Bill 1450 tomorrow`
"""

RECURRING_FEATURES = """
**Recurring Payments** automate regular expenses:
- Set up a recurring transaction for things that repeat — like monthly rent, weekly groceries, etc.
- Choose how often it repeats: daily, weekly, monthly, or yearly
- The app auto-logs the transaction on the due date, so you don't have to remember
- You can edit or delete recurring setups anytime

**Telegram shortcut:** `recurring Rent 15000 monthly bank`
"""

SUBSCRIPTION_FEATURES = """
The **Subscriptions** page tracks all your active subscriptions:
- Add subscriptions like Netflix, Spotify, YouTube Premium, etc.
- Set the billing cycle (monthly, yearly), amount, and renewal date
- Get alerted before a subscription renews so you're never surprised
- See all your subscriptions in one place with renewal dates

**Telegram shortcut:** `sub Netflix 649 card monthly`
"""

EMI_FEATURES = """
The **EMIs** page is for tracking loan installments:
- Add an EMI with the loan name, bank/lender, loan amount, interest rate, monthly installment, start date, and tenure
- Track how many months are remaining and what the total repayment will be
- See all your EMIs in one organized list with due dates

**Telegram shortcut:** `emi Car Loan 8500 netbanking`
"""

LOANS_FEATURES = """
The **Loans** page gives you a comprehensive view of all borrowing:
- It combines your EMIs and debts into one place so you can see your total outstanding amount
- A built-in **Loan EMI Calculator** lets you calculate monthly installments — enter loan amount, interest rate, and tenure, and it shows you the exact EMI, total interest, and full repayment schedule (amortization table)
- You can save a calculated loan directly from the calculator into your EMI tracking list
"""

DEBT_FEATURES = """
The **Debt** page tracks money you owe to someone (or someone owes you):
- Record debts with the person's name, amount, due date, interest rate, and minimum payment
- Mark a debt as paid once settled
- Track partial payments
- All unpaid debts appear in the Loans summary too

**Telegram shortcut:** `debt John 2000 cash borrowed` or `debt John 5000 upi lent` (for money someone owes you)
"""

TELEGRAM_BOT_FEATURES = """
The **ExpenseTracker Telegram Bot** (@expensetrackertnbot) is the fastest way to log transactions:
- Link your Telegram account to ExpenseTracker in just a few steps (no complicated setup)
- Once linked, just send a message like `Coffee 80` and it instantly logs an expense
- Supports logging expenses, income, budgets, goals, reminders, subscriptions, EMIs, debts, and categories
- All messages sync in real-time to your ExpenseTracker account
- You can use it from your phone, anywhere, without opening the app
"""

AUDIT_LOG_FEATURES = """
**Audit Logs** (also called Activity History) give you a full record of everything that's happened in your account:
- See every transaction that was added, edited, or deleted — with a timestamp
- Filter by type: Transactions, Budgets & Goals, Schedules & Reminders, or System Settings
- This helps you spot any mistakes or check what changed and when
- You can view up to the 250 most recent activities
"""

PROFILE_FEATURES = """
The **Profile** page is where you personalize your account:
- Update your display name
- Choose your preferred currency (INR, USD, EUR, GBP, JPY, AUD, CAD)
- Set your timezone so dates and times display correctly for you
- Toggle between **Dark Mode** and **Light Mode**
- **Export your data** — download all your expenses as a CSV or Excel file, filtered by today, this week, this month, last month, or a custom date range
- **Import expenses** — upload a CSV file to bulk-add past expenses
"""

HELP_FAQ_FEATURES = """
The **Help & FAQ** page has answers to the most common questions about using ExpenseTracker — covering account setup, features, the Telegram bot, data export, and more.
"""

SUPPORT_FEEDBACK_FEATURES = """
The **Support & Feedback** page is the best way to reach the team:
- Submit a bug report, feature request, or general question directly from within the app
- Rate your experience with a star rating
- Your request is sent instantly to the admin and you'll hear back via email
- This is the most effective support channel — faster than email
"""

UPDATES_FEATURES = """
The **Updates** page (available from the sidebar on mobile) shows a timeline of all ExpenseTracker version releases — what's new, what was fixed, and what was improved, with dates and version numbers.
"""

APP_SHORTCUT_FEATURES = """
ExpenseTracker is not listed on the Google Play Store or Apple App Store, but you can install it directly onto your phone or computer home screen. Once installed, it opens full-screen and works just like a regular app.

**The Easiest Way to Install:**
- Simply click the **"Install App"** button at the bottom of the sidebar menu.

**Alternative Browser Methods (if you don't see the sidebar button):**
- 📱 **Android (Chrome / Edge):** Tap the three dots in the top-right corner of Chrome, then select **"Install app"** or **"Add to Home screen"**.
- 🍏 **iPhone / iPad (Safari):** Tap the **"Share"** button (the square icon with an up arrow) at the bottom of Safari, scroll down, and tap **"Add to Home Screen"**.
- 💻 **Desktop (Chrome / Edge):** Click the **"Install App"** icon in the address bar at the top of the browser.
"""


# ─── Telegram Setup Guide ─────────────────────────────────────────────────────

TELEGRAM_SETUP_GUIDE = """
Here's how to link your Telegram account to ExpenseTracker:
1. Open Telegram and search for **@expensetrackertnbot**, or tap this link: [t.me/expensetrackertnbot](https://t.me/expensetrackertnbot)
2. Send the bot the command `/start` — it will reply with your unique **Chat ID** (a number like `123456789`)
3. Log in to ExpenseTracker at [expensetrackertn.vercel.app](https://expensetrackertn.vercel.app)
4. Go to **ExpenseTracker Bot** in the sidebar
5. Paste your Chat ID into the field and click **Link Telegram Account**
6. The bot will confirm the connection — and you're ready to start logging instantly!
"""

# ─── Telegram Logging Syntax ──────────────────────────────────────────────────

TELEGRAM_LOGGING_SYNTAX = """
Just send a plain message to the bot — no commands needed for most things.

**Basic format:** `title amount payment-mode note`

**Examples by type:**
- **Expense** (default — no prefix needed): `Coffee 80 upi` or `Lunch 250 cash for team`
- **Income** (use `income` or `inc`): `income Salary 50000 bank`
- **Category** (use `category` or `cat`): `category Medical` or `category Medical cross` (specifies category name and custom icon)
- **Budget** (use `budget`): `budget Food 5000` or `budget 30000` (global limit)
- **Recurring** (use `recurring` or `recur`): `recurring Rent 15000 monthly bank`
- **Goal** (use `goal` or `saving`): `goal New Laptop 95000`
- **Subscription** (use `sub` or `subscription`): `sub Netflix 649 card monthly`
- **EMI** (use `emi`): `emi Car Loan 8500 netbanking`
- **Debt** (use `debt`): `debt John 2000 cash borrowed for trip`
- **Reminder** (use `remind` or `reminder`): `remind Electricity Bill 1450 tomorrow`

Payment mode is optional — UPI is the default if you leave it out.
"""

# ─── Support Contact ──────────────────────────────────────────────────────────

SUPPORT_CONTACT = {
    "email": "r.r.kabilan0335@gmail.com",
    "bot_handle": "@expensetrackertnbot",
    "support_page": "https://expensetrackertn.vercel.app/support"
}

# ─── Redirect blocks for off-topic queries ────────────────────────────────────

REDIRECT_BLOCK = f"""ExpenseTracker (with MoneyCommandAI) can help you:
- 📊 Track expenses, income, budgets, goals, EMIs, and debts in one place
- ⚡ Log transactions instantly via Telegram — just send a quick message
- 📥 Export your data to Excel or CSV anytime
"""

REDIRECT_FEATURES = """- 📊 **Visual Dashboard:** See your spending trends, category breakdowns, and budget usage at a glance with interactive charts
- 🎯 **Budgets & Goals:** Set monthly spending limits and track progress towards financial goals like buying a phone or saving for a trip
- 📥 **Export Reports:** Download your full transaction history as Excel or CSV — filtered by date range"""

REDIRECT_TELEGRAM = """- ⚡ **Instant Logging via Telegram:** Just send `Coffee 80` to the bot and it logs an expense — no need to open the app
- 🔗 **Easy Setup:** Link your account in under 2 minutes using your Telegram Chat ID
- 🛠️ **10 Transaction Types Supported:** Log expenses, income, budgets, goals, reminders, EMIs, debts, and more — all from Telegram"""
