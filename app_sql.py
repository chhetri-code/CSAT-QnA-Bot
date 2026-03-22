import sqlite3
import random
from faker import Faker

# Connect to SQLite
connection = sqlite3.connect("csat.db")
cursor = connection.cursor()

# Drop table if exists
cursor.execute("DROP TABLE IF EXISTS CSAT")

# Create table
cursor.execute("""
    CREATE TABLE CSAT(
        Resp_ID INTEGER PRIMARY KEY,
        Vertical TEXT,
        Account TEXT,
        C_Name TEXT,
        C_Email TEXT,
        C_Desig TEXT,
        C_Geo TEXT,
        Response_Status TEXT,
        Rating INTEGER,
        Rating_Category TEXT,
        Feedback TEXT
    )
""")

fake = Faker()
num_rows = 225

# -------------------------------
# Account → Vertical mapping
# -------------------------------
accounts_verticals = {
    'Walmart': 'Retail',
    'Dollar General': 'Retail',
    'Ebay': 'Retail',
    'Target': 'Retail',
    '7-11': 'Retail',
    'SuperDry': 'Retail',
    'Panera': 'Retail',
    'Pfizer': 'Healthcare',
    'BMS': 'Healthcare',
    'Sanofi': 'Healthcare',
    'CVS': 'Healthcare'
}

# -------------------------------
# Account size distribution
# -------------------------------
account_weights = {
    'Walmart': 0.25,
    'Target': 0.10,
    'Ebay': 0.08,
    '7-11': 0.05,
    'SuperDry': 0.05,
    'Panera': 0.02,
    'Dollar General': 0.15,
    'Pfizer': 0.15,
    'BMS': 0.06,
    'Sanofi': 0.05,
    'CVS': 0.04
}

designations = ['Manager', 'Director', 'VP', 'Data Lead', 'Product Owner']
designation_weights = [0.40, 0.08, 0.12, 0.14, 0.16]

geographies = ['US', 'UK', 'Canada', 'Germany', 'India']
geo_weights = [0.75, 0.1, 0.07, 0.05, 0.03]

feedback_samples = [
    "AI service very responsive and accurate.",
    "Excellent support and automation.",
    "Very helpful insights provided.",
    "AI recommendations saved us a lot of time.",
    "Satisfied with service, minor improvements needed.",
    "Team is very proactive and solution-oriented.",
    "Interface is intuitive and easy to use.",
    "Love the predictive capabilities of the AI.",
    # Neutral
    "Could improve speed of recommendations.",
    "Occasionally data seems off, need refinement.",
    "Service is okay, nothing exceptional.",
    "Sometimes AI suggestions are generic.",
    "Good service but room for optimization.",
    # Negative
    "AI insights are not accurate for our needs.",
    "Support response time is too slow.",
    "Difficult to understand analytics outputs.",
    "Occasionally system crashes or errors.",
    "AI recommendations often irrelevant.",
    "Expecting more actionable insights from AI."
]


# -------------------------------
# Stratified Response Probability
# -------------------------------
def get_response_probability(account, geo, designation):
    prob = 0.60  # base

    # Geography effect
    if geo == 'US':
        prob += 0.10
    elif geo == 'India':
        prob -= 0.10

    # Designation effect
    if designation in ['VP', 'Director']:
        prob -= 0.15
    elif designation == 'Manager':
        prob += 0.05

    # Account engagement
    low_response_accounts = ['Dollar General', 'BMS']
    high_response_accounts = ['Walmart', 'Pfizer']
    if account in low_response_accounts:
        prob -= 0.15
    elif account in high_response_accounts:
        prob += 0.10

    return max(0.2, min(prob, 0.9))


# -------------------------------
# CSAT Generator (biased by account)
# -------------------------------
def generate_csat(account):
    if account in ['Ebay', 'Sanofi']:
        weights = [0.45, 0.35, 0.20]  # worse NPS
    else:
        weights = [0.65, 0.25, 0.10]

    category = random.choices(['Promoter', 'Passive', 'Detractor'], weights=weights)[0]

    if category == 'Promoter':
        return random.randint(9, 10)
    elif category == 'Passive':
        return random.randint(7, 8)
    else:
        return random.randint(0, 6)


def csat_category(score):
    if score >= 9:
        return 'Promoter'
    elif score >= 7:
        return 'Passive'
    else:
        return 'Detractor'


# -------------------------------
# Data Generation Loop
# -------------------------------
for i in range(1, num_rows + 1):
    # Account selection (non-uniform)
    account = random.choices(
        list(account_weights.keys()),
        weights=list(account_weights.values())
    )[0]

    vertical = accounts_verticals[account]
    client_name = fake.name()
    client_email = fake.email()
    client_designation = random.choices(designations, weights=designation_weights)[0]
    client_geo = random.choices(geographies, weights=geo_weights)[0]

    # Stratified response
    response_prob = get_response_probability(account, client_geo, client_designation)
    response_status = 'Submitted' if random.random() < response_prob else 'Did not submit'

    if response_status == 'Submitted':
        csat_rating = generate_csat(account)
        csat_cat = csat_category(csat_rating)
        feedback = random.choice(feedback_samples)
    else:
        csat_rating = None
        csat_cat = None
        feedback = None

    cursor.execute(
        "INSERT INTO CSAT VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (i, vertical, account, client_name, client_email, client_designation,
         client_geo, response_status, csat_rating, csat_cat, feedback)
    )

# -------------------------------
# Preview Data
# -------------------------------
print("Sample records:")
for row in cursor.execute("SELECT * FROM CSAT LIMIT 10"):
    print(row)

connection.commit()
connection.close()