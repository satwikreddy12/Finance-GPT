# 💰 Financial GPT Assistant

## Overview

Financial GPT is an AI-powered financial chatbot that helps users make smarter money decisions. Built with advanced NLP models and intuitive UI powered by Streamlit, it integrates diverse financial tools and agents to handle everything from budget management to stock forecasting.

## 🚀 Key Features

* **Budget & Expense Tracking**: Easily log and review your incomes, expenses, and investments.
* **Stock Market Insights**: Fetch real-time prices, analyst recommendations, and predictive stock forecasting using Prophet and Finnhub.
* **Loan Management Advice**: Calculate optimal debt repayment strategies (Avalanche & Snowball).
* **Credit Score Education**: Personalized advice to improve and manage your credit score.
* **Financial Planning Tools**: Calculate Debt-to-Income ratios, inflation impacts, and net worth summaries.
* **Sentiment Analysis**: Gauge market sentiment from latest news headlines.
* **General Financial Literacy**: Simplified explanations of financial concepts through practical analogies and actionable tips.

## 🛠️ Technology Stack

* **Frontend**: Streamlit
* **Backend**: Python, SQLite
* **Data & Analysis**:

  * `yfinance`, `finnhub` for market data
  * `prophet` for forecasting
  * `TextBlob` for sentiment analysis
* **AI Models**:

  * Groq Llama 3.3 (70B Versatile)
  * Phidata Agents (Phi framework)
* **Visualization**:

  * Matplotlib

## 🎯 Usage

### Installation

Clone this repository:

```bash
git clone https://github.com/yourusername/financial-gpt.git
cd financial-gpt
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the App

Launch Streamlit:

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501`

## 📺 Interface

* **Intuitive UI**: Select different financial categories through simple navigation.
* **Real-time Interaction**: Engage in natural language conversations with GPT.
* **Visualization & Reporting**: View detailed graphical forecasts and summaries.

## 📂 Project Structure

```
financial-gpt/
├── app.py                      # Streamlit UI
├── excercise2.py               # Main chatbot logic
├── budget.db                   # SQLite database for transaction records
├── agents.db                   # SQLite database for agents
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

## 🧩 Agents and Responsibilities

* **Finance Agent**: Stock price queries and forecasting
* **Budget Assistant**: Income, expense, and investment tracking
* **Loan Coach**: Debt repayment advice
* **Credit Score Advisor**: Credit education and improvement tips
* **Financial Planner**: Personal finance metrics calculations (DTI, inflation, net worth)
* **Sentiment Agent**: News-driven market sentiment analysis
* **Financial Literacy Coach**: Simplified explanations of financial concepts
* **Web Agent**: General queries requiring real-time web research
* **General Chat Agent**: Casual conversation and fallback queries

## 📸 Screenshot

![Github Pic](https://github.com/user-attachments/assets/0d872c4b-e88b-401f-9aec-47da26544094)


## 🤝 Contribution

Feel free to contribute! Open an issue or submit a pull request.
