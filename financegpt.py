import datetime
import sqlite3
import pandas as pd
import yfinance as yf
from textblob import TextBlob
from dotenv import load_dotenv

from phi.tools import tool
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.yfinance import YFinanceTools
from phi.storage.agent.sqlite import SqlAgentStorage
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

# Load environment variables
load_dotenv()

# --- Utility: map company name to symbol ------------------------------------------------
def get_company_symbol(company: str) -> str:
    symbols = {
        "Infosys": "INFY", "Tesla": "TSLA",
        "Apple": "AAPL",   "Microsoft": "MSFT", "Amazon": "AMZN", "Google": "GOOGL",
    }
    if company in symbols:
        return symbols[company]
    try:
        info = yf.Ticker(company).info
        return info.get("symbol", "Unknown")
    except Exception:
        return "Unknown"

# --- SQLite setup for transactions ------------------------------------------------------
conn = sqlite3.connect("budget.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        type TEXT,
        category TEXT,
        amount REAL
    )
    """
)
conn.commit()

# --- Tools -------------------------------------------------------------------------------

@tool
def add_transaction(
    type: str,
    category: str,
    amount: float,
    date: str | None = None  # new optional param
) -> str:
    # if user passed a date or month, use that, otherwise today
    if date:
        # try to parse “April 2025” → “2025-04-01”
        try:
            dt = date_parser.parse(date)
            date_str = dt.strftime("%Y-%m-%d")
        except:
            date_str = date  # assume already “YYYY-MM-DD”
    else:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        "INSERT INTO transactions (date, type, category, amount) VALUES (?, ?, ?, ?)",
        (date_str, type.lower(), category, amount)
    )
    conn.commit()
    return f"Recorded {type.title()} of ${amount:.2f} under '{category}' on {date_str}."


@tool
def list_transactions() -> str:
    """
    Return a table of all transactions including their internal ID,
    date, type, category, and amount.
    """
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    if df.empty:
        return "No transactions recorded yet."
    # show only first 100 rows if too large
    df = df[['id','date','type','category','amount']]
    return df.to_string(index=False)

@tool
def delete_transaction(record_id: int) -> str:
    """
    Delete a single transaction by its ID.
    """
    cursor.execute("DELETE FROM transactions WHERE id = ?", (record_id,))
    conn.commit()
    return f"Deleted transaction with id {record_id}."

@tool
def clear_transactions() -> str:
    """
    Delete all transactions and start fresh.
    """
    cursor.execute("DELETE FROM transactions")
    conn.commit()
    return "All transactions have been cleared."


@tool
def get_budget_summary(months: list[str] = None) -> str:
    """
    Summarize income & expenses for one or more YYYY-MM months.
    If months is None: all-time.
    """
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    if df.empty:
        return "No transactions recorded yet."

    df['date'] = pd.to_datetime(df['date'])
    if months:
        # normalize input like ["April","May"] → ["2025-04","2025-05"]
        normalized = []
        for m in months:
            try:
                dt = date_parser.parse(m)
                normalized.append(dt.strftime("%Y-%m"))
            except:
                # if already YYYY-MM
                normalized.append(m)
        df = df[df['date'].dt.strftime("%Y-%m").isin(normalized)]

    total_inc = df[df['type']=="income"]['amount'].sum()
    total_exp = df[df['type']=="expense"]['amount'].sum()
    balance   = total_inc - total_exp

    label = ", ".join(months) if months else "all time"
    text  = f"📊 Budget Summary for {label}:\n\n"
    text += f"• Income:  ${total_inc:.2f}\n"
    text += f"• Expenses:${total_exp:.2f}\n"
    text += f"• Balance: ${balance:.2f}\n\n"

    brkd = df[df['type']=="expense"].groupby('category')['amount'].sum().reset_index()
    text += "Expense Breakdown:\n" + brkd.to_string(index=False)
    return text

@tool
def calculate_loan_repayment(loans: list[dict], strategy: str = "avalanche") -> str:
    df = pd.DataFrame(loans)
    if strategy.lower() == "avalanche":
        df = df.sort_values(by="rate", ascending=False)
    else:
        df = df.sort_values(by="balance")
    text = f"Repayment Strategy: {strategy.title()}\n\n" + df.to_string(index=False)
    text += "\n\nTip: Pay minimums on all loans, then put extra toward the top loan."
    return text

@tool
def inflation_adjusted_value(amount: float, years: int, inflation_rate: float = 3.0) -> str:
    adjusted = amount / ((1 + inflation_rate/100) ** years)
    return f"${amount:.2f} will be worth approximately ${adjusted:.2f} in {years} years at {inflation_rate:.1f}% inflation." 

@tool
def dti_ratio(monthly_debt: float, monthly_income: float) -> str:
    if monthly_income <= 0:
        return "Income must be greater than zero."
    ratio = (monthly_debt / monthly_income) * 100
    return f"Your Debt-to-Income ratio is {ratio:.2f}%. Below 36% is considered healthy."

@tool
def calculate_net_worth(assets: dict, liabilities: dict) -> str:
    total_assets = sum(assets.values())
    total_liabilities = sum(liabilities.values())
    net_worth = total_assets - total_liabilities
    return (
        f"Total Assets: ${total_assets:,.2f}\n"
        f"Total Liabilities: ${total_liabilities:,.2f}\n"
        f"Net Worth: ${net_worth:,.2f}"
    )

@tool
def analyze_sentiment(headlines: list[str]) -> str:
    if not headlines:
        return "No headlines provided."
    scores = [TextBlob(h).sentiment.polarity for h in headlines]
    avg = sum(scores) / len(scores)
    mood = "Positive" if avg > 0.2 else "Negative" if avg < -0.2 else "Neutral"
    return f"Overall Sentiment: {mood} (avg polarity: {avg:.2f})"

@tool
def get_investment_summary() -> str:
    """
    Summarize all logged 'investment' expenses, grouped by category.
    """
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    if df.empty:
        return "No transactions recorded yet."
    inv = df[df['category'].str.contains("investment", case=False, na=False)]
    if inv.empty:
        return "No investment transactions found."
    total = inv['amount'].sum()
    brkd  = inv.groupby('category')['amount'].sum().reset_index()
    text  = f"💰 Total Invested: ${total:.2f}\n\nBreakdown:\n" + brkd.to_string(index=False)
    return text

@tool
def list_investments() -> str:
    """
    Show raw investment rows with date, category, amount & id.
    """
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    if df.empty:
        return "No transactions recorded yet."
    inv = df[df['category'].str.contains("investment", case=False, na=False)]
    if inv.empty:
        return "No investments found."
    return inv[['id','date','category','amount']].to_string(index=False)

# --- Agents --------------------------------------------------------------------------------

web_agent = Agent(
    name="Web Agent",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[DuckDuckGo()],
    instructions=[
        "Identify factual questions requiring web research (e.g. ‘latest news’, ‘benefits of X’)",
        "Disambiguate requests (e.g., company names vs. product names) by asking clarifying questions if unclear.",
        "Perform DuckDuckGo search, gather up to 5 reputable sources (.gov, .edu, major media)",
        "Synthesize into 2–4 bullet points, citing each source URL.",
        "Handle rephrased or slang queries gracefully by mapping synonyms and paraphrases."
        "If the question not understood, ask to write the question again",
        "Keep answers succinct and up-to-date."
    ],
    show_tool_calls=False,
    markdown=True
)

finance_agent = Agent(
    name="Finance Agent",
    role="Get stock prices and analyst recommendations",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True)],
    instructions=[
        "Interpret various phrasings (e.g. 'NVDA quote', 'price of Nvidia') and confirm ticker if ambiguous.",
        "Display latest price, % change, volume in a table; summarize analyst ratings with clear labels.",
        "Detect stock or company data requests (prices, ratings, metrics)",
        "Present in a table: price, % change, volume, consensus ratings",
        "If user asks for historical or specific periods, fetch data accordingly and explain trends.",
        "If business overview requested, give a 2-3 sentence summary.",
        "Offer brief business summary when asked (sector, market cap, key products)."  
    ],
    show_tool_calls=False,
    markdown=True
)

financial_literacy_agent = Agent(
    name="Financial Literacy Coach",
    role="Explain finance concepts simply",
    model=Groq(id="llama-3.3-70b-versatile"),
    instructions=[
        "Recognize twisted or colloquial finance questions and map them to core concepts.",
        "Break down explanations into 3 simple steps, using everyday analogies.",
        "Explain the concept with a small example in a simple way"
        "Ask follow-up questions if user context (goal, timeframe) is needed.",
        "Always conclude with a clear action tip or takeaway.",
        "Handle multi-turn concept deep dives by retaining context across questions."
    ],
    show_tool_calls=False,
    markdown=True
)


budget_agent = Agent(
    name="Budget & Investment Assistant",
    role="Track income, expenses & investments; support multi‑month summaries",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[
        add_transaction,
        get_budget_summary,
        get_investment_summary,
        list_investments,
        delete_transaction,
        clear_transactions
    ],
    instructions=[
      # logging
      "When user says 'I spent', 'I paid', 'I earned', or 'I invested', extract type, amount, category and optional month(s).",
      "Treat 'invested' exactly like an expense but append 'investment' to category if none given.",
      "When the user says things like 'Earned', 'spent', 'paid', or 'invested', extract type (expense for spent/invested, income for received), category, amount, and optional period.",
      "Earned means income",
      "If the user mentions a period (e.g. ‘in April’, ‘on 2025-04-15’), parse it, then call add_transaction(type, category, amount, date=parsed_date) rather than the old 3-arg call",
      "If user just says 'I want to invest', ask: 'Sure—what would you like to invest in, and how much?'",
      "Support natural month names and comma/separated lists (e.g. 'April and May', '2025‑04,2025‑05').",
      "Convert months to YYYY-MM before calling tools.",
      "After logging, reply 'Recorded [type] of $X under “[category]” for [month].'",

      # summaries
      "If user asks 'budget summary' with month(s), call get_budget_summary(months=list).",
      "If no month given, call get_budget_summary() for all time.",
      "Return the tool's output exactly—no extra wrapping.",

      # investments
      "If user asks 'investment summary' or 'show investments', call get_investment_summary().",
      "If user asks 'list my investments', call list_investments().",

      # delete / clear
      "If user says 'delete transaction <id>', call delete_transaction(id) and confirm.",
      "If user says 'clear all transactions' or similar, call clear_transactions() and confirm.",

      # clarifications
      "If key info (amount, category, or month) is missing or ambiguous, ask a brief follow‑up question."
    ],
    show_tool_calls=False,
    markdown=True
)


loan_agent = Agent(
    name="Loan Coach",
    role="Advise on debt repayment strategies",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[calculate_loan_repayment],
    instructions=[
        "Extract loan name, balance, rate, min payment from user input",
        "Extract loan details from varied user inputs (multiple loans, partial info).",
        "If details are incomplete, ask for missing balances, rates, or min payments.",
        "Explain both avalanche and snowball methods, then recommend based on user goals.",
        "When chosen, call calculate_loan_repayment and interpret the table for next steps." 
        "Explain avalanche vs snowball with pros/cons",
        "If method specified, call calculate_loan_repayment accordingly; else default to avalanche."  
    ],
    show_tool_calls=False,
    markdown=True
)

credit_score_agent = Agent(
    name="Credit Score Advisor",
    role="Educate on credit scores and improvement",
    model=Groq(id="llama-3.3-70b-versatile"),
    instructions=[
        "Answer both general and technical credit score queries, defining terms clearly.",
        "Tailor tips to user’s situation if they mention debts or payment history.",
        "Offer short-term and long-term improvement strategies.",
        "Answer situational questions also"
        "Handle follow-up questions by recalling prior credit context in the session."
    ],
    show_tool_calls=False,
    markdown=True
)

general_chat_agent = Agent(
    name="General Chat Agent",
    role="Handle greetings and basic fallback queries",
    model=Groq(id="llama-3.3-70b-versatile"),
    instructions=[
        "Handle greetings, small talk, and 'who are you' questions directly.",
        "For off-topic queries, politely state limitations and suggest finance-related topics.",
        "If the query hints at a finance request, route to the appropriate specialist agent."
    ],
    show_tool_calls=False,
    markdown=True
)

financial_planner_agent = Agent(
    name="Financial Planner",
    role="Handle DTI, inflation, net worth calculations",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[dti_ratio, inflation_adjusted_value, calculate_net_worth],
    instructions=[
        "Check Carefully what the questions is,which tool is it related to"
        "If the answer requires 2 or more tools, combine them if needed"
        "Detect mixed planning requests (e.g., 'net worth and inflation impact') and split into steps.",
        "Call each relevant tool, then combine results into a cohesive plan.",
        "Explain numeric outputs in plain language with next-action suggestions."
    ],
    show_tool_calls=False,
    markdown=True
)

sentiment_agent = Agent(
    name="Sentiment Agent",
    role="Analyze news sentiment",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[DuckDuckGo(), analyze_sentiment],
    instructions=[
        "Fetch the 5 latest headlines about the company via DuckDuckGo",
        "Call analyze_sentiment(headlines) for overall polarity",
        "Return headlines list and sentiment summary in plain text"
        "Give suggestion on if the stock can be buyed or not"
        "If headlines are unclear or misleading, ask user to clarify topic."
    ],
    show_tool_calls=False,
    markdown=True
)

# --- Master Agent Team ---------------------------------------------------------

agent_team = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    team=[
        web_agent,
        finance_agent,
        financial_literacy_agent,
        budget_agent,
        loan_agent,
        credit_score_agent,
        general_chat_agent,
        financial_planner_agent,
        sentiment_agent
    ],
    instructions=[
        "Parse user intent and route to the correct agent:",
        "- Greetings → General Chat Agent",
        "First, determine if the question is general, conceptual, transactional, strategic, or data-driven.",
        "Use General Chat for greetings/fallbacks; Literacy for concepts; Budget for transactions/summaries;",
        "Loan for debt strategies; Credit Score for scoring advice; Planner for health metrics; Sentiment for news mood;",
        "Finance for stock/company data; Web for anything else requiring search.",
        "If user phrasing is unclear or uses slang, ask a brief clarifying question before proceeding.",
        "Always output a clean, user-friendly answer without exposing internal tool JSON." 
        "- Finance concepts → Financial Literacy Coach",
        "- Transactions/summary → Budget Assistant",
        "- Debt strategies → Loan Coach",
        "- Credit advice → Credit Score Advisor",
        "- Planning (DTI, inflation, net worth) → Financial Planner",
        "- Stock data → Finance Agent",
        "- News sentiment → Sentiment Agent",
        "- Otherwise → Web Agent",
        "Execute any needed tools and return clean, human-readable answers without raw tool JSON."
    ],
    show_tool_calls=False,
    storage=SqlAgentStorage(table_name="agent_team", db_file="agents.db"),
    add_history_to_messages=True,
    markdown=True
)
