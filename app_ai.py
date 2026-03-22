###############################################################################
#### CSAT GenAI (Text to SQL using Groq LLaMA) ################################
###############################################################################


import os
import re
import sqlite3
import pandas as pd
from typing import List, Optional
from groq import Groq
import streamlit as st


# Initialize Groq client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])


###############################################################################
# 🧹 SQL CLEANER — strips LLM markdown fences and whitespace
###############################################################################
def clean_sql(sql: str) -> str:
    """Remove markdown code fences and extra whitespace from LLM SQL output."""
    sql = re.sub(r"```(?:sql)?", "", sql, flags=re.IGNORECASE)
    sql = sql.replace("`", "").strip()
    return sql


###############################################################################
# 🚀 LOCAL SQL GENERATOR — handles common queries without any API call
###############################################################################
def local_sql_generator(question: str) -> Optional[str]:
    """
    Handles frequently asked questions locally to avoid API calls entirely.

    Parameters
    ----------
    question : str
        User's natural language question.

    Returns
    -------
    Optional[str]
        SQL string if matched locally, else None to fall through to LLM.
    """
    q = question.lower().strip()

    # Total clients / headcount
    if any(p in q for p in ["total clients", "total people", "how many clients", "total headcount"]):
        return "SELECT COUNT(*) AS TotalClients FROM csat"

    # Responded / submitted
    if any(p in q for p in ["how many responded", "who responded", "total responses", "submitted"]):
        return "SELECT COUNT(*) AS RespondedClients FROM csat WHERE Response_Status = 'Submitted'"

    # Response rate
    if any(p in q for p in ["response rate", "participation rate"]):
        return (
            "SELECT "
            "COUNT(*) AS TotalClients, "
            "SUM(CASE WHEN Response_Status = 'Submitted' THEN 1 ELSE 0 END) AS Responded, "
            "ROUND(100.0 * SUM(CASE WHEN Response_Status = 'Submitted' THEN 1 ELSE 0 END) / COUNT(*), 2) AS ResponseRatePct "
            "FROM csat"
        )

    # Overall NPS (no grouping)
    if ("nps" in q or "net promoter" in q) and not any(p in q for p in ["by account", "by vertical", "by geo", "by desig", "breakdown"]):
        return (
            "SELECT "
            "SUM(CASE WHEN Rating_Category = 'Promoter'  THEN 1 ELSE 0 END) AS Promoters, "
            "SUM(CASE WHEN Rating_Category = 'Passive'   THEN 1 ELSE 0 END) AS Passives, "
            "SUM(CASE WHEN Rating_Category = 'Detractor' THEN 1 ELSE 0 END) AS Detractors, "
            "ROUND(100.0 * ("
            "SUM(CASE WHEN Rating_Category = 'Promoter' THEN 1 ELSE 0 END) - "
            "SUM(CASE WHEN Rating_Category = 'Detractor' THEN 1 ELSE 0 END)"
            ") / COUNT(*), 2) AS NPS "
            "FROM csat WHERE Response_Status = 'Submitted'"
        )

    # NPS by account
    if ("nps" in q or "net promoter" in q) and "account" in q:
        return (
            "SELECT Account, "
            "SUM(CASE WHEN Rating_Category = 'Promoter'  THEN 1 ELSE 0 END) AS Promoters, "
            "SUM(CASE WHEN Rating_Category = 'Passive'   THEN 1 ELSE 0 END) AS Passives, "
            "SUM(CASE WHEN Rating_Category = 'Detractor' THEN 1 ELSE 0 END) AS Detractors, "
            "ROUND(100.0 * ("
            "SUM(CASE WHEN Rating_Category = 'Promoter' THEN 1 ELSE 0 END) - "
            "SUM(CASE WHEN Rating_Category = 'Detractor' THEN 1 ELSE 0 END)"
            ") / COUNT(*), 2) AS NPS "
            "FROM csat WHERE Response_Status = 'Submitted' GROUP BY Account ORDER BY NPS DESC"
        )

    # NPS by vertical
    if ("nps" in q or "net promoter" in q) and "vertical" in q:
        return (
            "SELECT Vertical, "
            "SUM(CASE WHEN Rating_Category = 'Promoter'  THEN 1 ELSE 0 END) AS Promoters, "
            "SUM(CASE WHEN Rating_Category = 'Passive'   THEN 1 ELSE 0 END) AS Passives, "
            "SUM(CASE WHEN Rating_Category = 'Detractor' THEN 1 ELSE 0 END) AS Detractors, "
            "ROUND(100.0 * ("
            "SUM(CASE WHEN Rating_Category = 'Promoter' THEN 1 ELSE 0 END) - "
            "SUM(CASE WHEN Rating_Category = 'Detractor' THEN 1 ELSE 0 END)"
            ") / COUNT(*), 2) AS NPS "
            "FROM csat WHERE Response_Status = 'Submitted' GROUP BY Vertical ORDER BY NPS DESC"
        )

    # Promoter / Passive / Detractor breakdown
    if any(p in q for p in ["promoter", "passive", "detractor", "rating breakdown", "category breakdown"]):
        return (
            "SELECT Rating_Category, COUNT(*) AS Count "
            "FROM csat WHERE Response_Status = 'Submitted' GROUP BY Rating_Category"
        )

    # Responses by vertical
    if "vertical" in q and any(p in q for p in ["response", "count", "how many"]):
        return (
            "SELECT Vertical, COUNT(*) AS Responses "
            "FROM csat WHERE Response_Status = 'Submitted' GROUP BY Vertical ORDER BY Responses DESC"
        )

    # Responses by account
    if "account" in q and any(p in q for p in ["response", "count", "how many"]):
        return (
            "SELECT Account, COUNT(*) AS Responses "
            "FROM csat WHERE Response_Status = 'Submitted' GROUP BY Account ORDER BY Responses DESC"
        )

    # Responses by geo
    if any(p in q for p in ["geo", "geography", "region", "location"]) and any(p in q for p in ["response", "count", "how many"]):
        return (
            "SELECT C_Geo, COUNT(*) AS Responses "
            "FROM csat WHERE Response_Status = 'Submitted' GROUP BY C_Geo ORDER BY Responses DESC"
        )

    # All feedback / comments
    if any(p in q for p in ["feedback", "comments", "what did they say", "verbatim"]):
        return (
            "SELECT Account, C_Name, Rating, Rating_Category, Feedback "
            "FROM csat WHERE Response_Status = 'Submitted' AND Feedback IS NOT NULL AND Feedback != '' "
            "ORDER BY Rating ASC"
        )

    # Detractors detail
    if "detractor" in q and any(p in q for p in ["list", "who", "show", "detail", "name"]):
        return (
            "SELECT Account, C_Name, C_Desig, Rating, Feedback "
            "FROM csat WHERE Rating_Category = 'Detractor' AND Response_Status = 'Submitted' "
            "ORDER BY Rating ASC"
        )

    # Promoters detail
    if "promoter" in q and any(p in q for p in ["list", "who", "show", "detail", "name"]):
        return (
            "SELECT Account, C_Name, C_Desig, Rating, Feedback "
            "FROM csat WHERE Rating_Category = 'Promoter' AND Response_Status = 'Submitted' "
            "ORDER BY Rating DESC"
        )

    # Did not respond / non-respondents
    if any(p in q for p in ["not responded", "did not respond", "non respondent", "pending"]):
        return (
            "SELECT Account, C_Name, C_Email, C_Desig "
            "FROM csat WHERE Response_Status != 'Submitted' ORDER BY Account"
        )

    return None  # No local match → fall through to LLM


###############################################################################
# 🤖 GROQ LLM CALL — only fires when local generator returns None
###############################################################################
def get_gemini_response(question: str, prompt: List[str]) -> str:
    """
    Converts a natural language question into SQL using Groq LLaMA.
    Function name kept as-is to avoid breaking the frontend.

    Parameters
    ----------
    question : str
        User's natural language question.
    prompt : List[str]
        System prompt with schema, rules, and few-shot examples.

    Returns
    -------
    str
        Clean SQL query string.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # Best Groq model for SQL generation
            messages=[
                {"role": "system", "content": prompt[0]},
                {"role": "user",   "content": question}
            ],
            temperature=0,      # Deterministic output — critical for SQL accuracy
            max_tokens=512,     # SQL rarely needs more; keeps responses fast
        )
        raw = response.choices[0].message.content.strip()
        return clean_sql(raw)
    except Exception as e:
        print(f"Groq API error: {e}")
        return "ERROR"


###############################################################################
# 🗄️ SQL EXECUTOR
###############################################################################
def read_sql_query(sql: str, db_file: str) -> pd.DataFrame:
    """
    Executes a SQL query on the specified SQLite database.

    Parameters
    ----------
    sql : str
        SQL query string (will be cleaned of any stray fences).
    db_file : str
        Path to SQLite database file.

    Returns
    -------
    pd.DataFrame
        Query results. Returns empty DataFrame on error.
    """
    sql = clean_sql(sql)  # Safety net — strips any leftover fences

    if not sql or sql.upper() == "ERROR":
        print("Received invalid SQL — skipping execution.")
        return pd.DataFrame()

    try:
        with sqlite3.connect(db_file) as conn:
            df = pd.read_sql_query(sql, conn)
    except Exception as e:
        print(f"SQL execution error: {e}")
        df = pd.DataFrame()
    return df


###############################################################################
# 🧠 MASTER SQL ROUTER
###############################################################################
def generate_sql(question: str, prompt: List[str]) -> str:
    """
    Routes question to local generator first; falls back to Groq LLM if needed.
    Local handling covers ~70% of common CSAT queries with zero API calls.
    """
    sql = local_sql_generator(question)
    if sql:
        return sql
    return get_gemini_response(question, prompt)


###############################################################################
# 📋 SYSTEM PROMPT — used only for queries not matched locally
###############################################################################
prompt = ["""
You are an expert SQL query generator for a SQLite database called csat.db.
TABLE: csat
COLUMNS:
    Resp_ID         INTEGER PRIMARY KEY
    Vertical        TEXT
    Account         TEXT
    C_Name          TEXT
    C_Email         TEXT
    C_Desig         TEXT
    C_Geo           TEXT
    Response_Status TEXT       -- values: 'Submitted' | 'Did not submit'
    Rating          INTEGER
    Rating_Category TEXT       -- values: 'Promoter' | 'Passive' | 'Detractor'
    Feedback        TEXT
RULES:
    - Output ONLY the raw SQL query — no backticks, no ```sql fences, no explanations.
    - Filter on Response_Status = 'Submitted' for all metrics EXCEPT total headcount.
    - Round all percentages and scores to 2 decimal places.
    - When reporting NPS, always include Promoter, Passive, and Detractor counts.
    - Use clear, intuitive column aliases.
    - Always add ORDER BY where results benefit from ranking.
    - ALWAYS wrap text column filters with UPPER(TRIM(...)) on both sides.
      Example: UPPER(TRIM(Account)) = UPPER(TRIM('ebay'))
      This handles case mismatches and accidental whitespace in both the data and user input.
NPS FORMULA:
    ROUND(100.0 * (Promoters - Detractors) / TotalRespondents, 2)
EXAMPLES:
-- Total clients
SELECT COUNT(*) AS TotalClients FROM csat;
-- Responded clients
SELECT COUNT(*) AS RespondedClients FROM csat WHERE UPPER(TRIM(Response_Status)) = 'SUBMITTED';
-- Overall NPS
SELECT
    SUM(CASE WHEN Rating_Category = 'Promoter'  THEN 1 ELSE 0 END) AS Promoters,
    SUM(CASE WHEN Rating_Category = 'Passive'   THEN 1 ELSE 0 END) AS Passives,
    SUM(CASE WHEN Rating_Category = 'Detractor' THEN 1 ELSE 0 END) AS Detractors,
    ROUND(100.0 * (
        SUM(CASE WHEN Rating_Category = 'Promoter'  THEN 1 ELSE 0 END) -
        SUM(CASE WHEN Rating_Category = 'Detractor' THEN 1 ELSE 0 END)
    ) / COUNT(*), 2) AS NPS
FROM csat
WHERE UPPER(TRIM(Response_Status)) = 'SUBMITTED';
-- NPS by account
SELECT Account,
    SUM(CASE WHEN Rating_Category = 'Promoter'  THEN 1 ELSE 0 END) AS Promoters,
    SUM(CASE WHEN Rating_Category = 'Passive'   THEN 1 ELSE 0 END) AS Passives,
    SUM(CASE WHEN Rating_Category = 'Detractor' THEN 1 ELSE 0 END) AS Detractors,
    ROUND(100.0 * (
        SUM(CASE WHEN Rating_Category = 'Promoter'  THEN 1 ELSE 0 END) -
        SUM(CASE WHEN Rating_Category = 'Detractor' THEN 1 ELSE 0 END)
    ) / COUNT(*), 2) AS NPS
FROM csat
WHERE UPPER(TRIM(Response_Status)) = 'SUBMITTED'
GROUP BY Account ORDER BY NPS DESC;
-- Client detail for a specific account
SELECT Vertical, Account, C_Name, Rating, Rating_Category, Feedback
FROM csat WHERE UPPER(TRIM(Account)) = UPPER(TRIM('Target'));"""]


###############################################################################
# 💬 GREETING MESSAGES
###############################################################################
greetings = [
    "Okay! Here you go...",
    "This is what I found:",
    "Alright! Have a look.",
    "I looked up in the database. This is what I found...",
    "I found this:",
    "Here you go!",
    "Here are the details. As you asked!",
    "I want to be a smart robot!",
    "I can tell you this:",
    "Hope this helps!"
]
