###############################################################################
# CSAT Data Generator (Realistic + Feedback aligned with NPS)
###############################################################################

import sqlite3
import random
from faker import Faker

# -------------------------------
# Connect to SQLite
# -------------------------------
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

# -------------------------------
# Feedback pools by sentiment
# -------------------------------
positive_feedback = [
    "The AI service has been remarkably responsive and accurate — it's genuinely transformed how our team approaches data-driven decisions on a daily basis.",
    "The support team has been excellent throughout our onboarding and beyond. Their automation solutions saved us countless hours of manual work every week.",
    "The insights provided have been incredibly helpful in identifying trends we would have otherwise missed. It feels like having an extra analyst on the team.",
    "The AI recommendations alone have saved us weeks of analysis time. Our team can now focus on strategy rather than crunching numbers endlessly.",
    "What really stands out is how proactive and solution-oriented the team is. They don't just respond to issues — they anticipate them and come prepared with fixes.",
    "The interface is beautifully intuitive and easy to navigate, even for team members who don't have a deep technical background. Adoption across our org was seamless.",
    "We absolutely love the predictive capabilities. The model accuracy has consistently impressed us, and it's given us a real competitive edge in forecasting.",
    "The dashboards are clean, well-organized, and genuinely easy to interpret. Our stakeholders can now review data independently without needing constant support from our data team.",
    "Onboarding was smooth and the documentation is thorough. We were up and running much faster than expected, which made a big difference for our project timelines.",
    "The platform integrates beautifully with our existing data stack. We saw measurable ROI within the first month of deployment, which exceeded our expectations entirely.",
    "The anomaly detection feature has been a game-changer for our operations team. We're now catching data irregularities in real time rather than discovering them days later in a quarterly review.",
    "Customer success manager has been outstanding — always available, deeply knowledgeable, and genuinely invested in making sure we're getting the most value out of the platform.",
    "The natural language querying feature is something our non-technical teams absolutely love. Being able to ask data questions in plain English and get meaningful answers instantly has democratized analytics across the whole organization.",
    "We've significantly reduced our dependency on external consultants since adopting this platform. The self-serve analytics capabilities have empowered our internal teams in a way we didn't think was possible this quickly.",
    "The custom model training options have allowed us to tailor the AI specifically to our business domain. The accuracy improvements we've seen after fine-tuning have been remarkable and well worth the effort.",
    "Reporting that used to take our team three full days now takes under an hour. The time savings are very real, and leadership has noticed the difference in how quickly we can respond to business questions.",
    "The segmentation and cohort analysis tools are incredibly powerful. We've uncovered customer behavior patterns that have directly influenced our product roadmap and go-to-market strategy.",
    "What surprised us most was how well the platform scales. As our data volumes have grown significantly over the past year, performance has remained consistently strong without any noticeable degradation.",
    "The automated alerting system has helped us stay on top of KPI fluctuations without having to manually monitor dashboards. It's saved us from several potential issues that could have escalated quickly.",
    "The team's domain expertise in our industry really sets them apart. They don't just deliver technical solutions — they ask the right business questions first, which leads to much more meaningful outcomes.",
]

neutral_feedback = [
    "Overall, we're fairly satisfied with the service, but there are a few minor improvements — particularly around data visualization — that would make a noticeable difference in our workflow.",
    "The quality of recommendations is solid, but the speed at which they're generated could definitely be improved. On larger datasets, the latency becomes a bit of a bottleneck.",
    "Occasionally, the data outputs seem slightly off or inconsistent, especially when working with edge cases. Some additional refinement and model tuning would go a long way here.",
    "The service is decent and meets our basic requirements, but it hasn't quite delivered the 'wow' factor we were hoping for. It does the job, but doesn't particularly stand out.",
    "Some of the AI suggestions feel a bit generic and don't always account for the nuances of our specific industry. More contextual customization options would be a welcome addition.",
    "It's a good service overall, but there's clear room for optimization — particularly in how the AI handles niche or unusual data patterns that fall outside standard training scenarios.",
    "The core features work well, but the reporting module feels somewhat underdeveloped compared to the rest of the platform. We expected a bit more depth in the export options.",
    "Customer support has been responsive, but the turnaround time on more complex technical queries tends to stretch longer than we'd prefer. A dedicated technical account manager would help.",
    "The platform covers our fundamental analytics needs adequately, but we've found ourselves supplementing it with other tools for more advanced statistical modeling. Better native support in that area would be ideal.",
    "The UI is functional and mostly clean, but the mobile experience feels noticeably underdeveloped. For a team that often reviews dashboards on the go, this is a limitation we run into regularly.",
    "The AI performs well on structured data, but we've noticed a drop in reliability when feeding in unstructured or semi-structured inputs. Improving that flexibility would significantly broaden its usefulness for us.",
    "Billing and subscription management could be much more transparent. We've had a couple of instances where usage-based charges were unclear, which caused some friction internally during budget reviews.",
    "The platform shows a lot of promise and the underlying technology is clearly solid, but the feature release cadence feels slower than what we were led to expect during the sales process.",
    "Training resources and tutorials are available but feel somewhat surface-level. We'd benefit greatly from more advanced documentation and real-world use case walkthroughs for complex analytical scenarios.",
    "The integration with our CRM works most of the time, but we've experienced occasional sync issues that require manual intervention. It's not a dealbreaker, but it does add unnecessary friction to our workflow.",
    "Data refresh rates are acceptable for most of our reporting needs, but near-real-time updates would make the platform significantly more valuable for our operations and customer-facing teams.",
]

negative_feedback = [
    "Unfortunately, the AI insights haven't been accurate enough for our specific use case. We've had to manually verify outputs regularly, which defeats the purpose of using an automated system.",
    "Support response times have been far too slow for a business-critical tool. When we're facing data pipeline issues, waiting 48+ hours for a resolution simply isn't acceptable.",
    "The analytics outputs are quite difficult to interpret without a strong data science background. Non-technical stakeholders on our team are struggling to extract actionable meaning from the reports.",
    "We've experienced several unexpected system crashes and errors over the past few months, causing significant disruptions to our reporting cycles. Stability needs to be a higher priority.",
    "The AI recommendations have often felt irrelevant to our business context. It seems like the model hasn't been well-calibrated to our industry, resulting in suggestions we can't realistically act on.",
    "We expected more concrete, actionable insights from the platform. Right now, the outputs feel more descriptive than prescriptive — we need recommendations that go beyond just summarizing what already happened.",
    "The pricing structure doesn't feel proportional to the value we're currently receiving. Several promised features are still in development, and the gaps are becoming harder to justify to leadership.",
    "There's a lack of transparency in how the AI arrives at its conclusions. Without explainability features or confidence scores, it's very difficult for our team to trust and act on the recommendations.",
    "Data ingestion has been a persistent pain point. We've had multiple instances where pipelines failed silently without any alerts or error logs, leaving our dashboards displaying stale data without us realizing it.",
    "The onboarding process was far more complicated than anticipated. We were largely left to figure things out on our own, and the documentation didn't cover enough of the edge cases our environment presented.",
    "We've raised the same data accuracy concern three times now, and while we always receive a polite acknowledgment, we haven't seen any meaningful changes or follow-through. It's becoming a trust issue.",
    "The platform struggles noticeably with high data volumes. During peak processing periods, performance degrades to the point where running reports becomes impractical and unreliable for time-sensitive decisions.",
    "The lack of role-based access controls at a granular level has become a real compliance concern for us. We need finer-grained permission settings to meet our internal data governance requirements.",
    "We were promised seamless integration with our existing BI tools during the sales process, but the reality has been far more manual and technically involved than described. Expectations were clearly mismanaged.",
    "The model retraining process is opaque and takes far too long. When our underlying business data changes significantly, there's no clear timeline or communication on when updated model behavior will take effect.",
    "Error messages in the platform are vague and unhelpful. When something goes wrong, our team has no way of diagnosing the issue independently, which means every minor problem turns into a support ticket.",
]
# -------------------------------
# Stratified Response Probability
# -------------------------------
def get_response_probability(account, geo, designation):
    prob = 0.60

    if geo == 'US':
        prob += 0.10
    elif geo == 'India':
        prob -= 0.10

    if designation in ['VP', 'Director']:
        prob -= 0.15
    elif designation == 'Manager':
        prob += 0.05

    low_response_accounts = ['Dollar General', 'BMS']
    high_response_accounts = ['Walmart', 'Pfizer']

    if account in low_response_accounts:
        prob -= 0.15
    elif account in high_response_accounts:
        prob += 0.10

    return max(0.2, min(prob, 0.9))

# -------------------------------
# CSAT Generator
# -------------------------------
def generate_csat(account):
    if account in ['Ebay', 'Sanofi']:
        weights = [0.45, 0.35, 0.20]  # worse accounts
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
# Feedback Generator (Aligned)
# -------------------------------
def generate_feedback(category, score):
    if category == 'Promoter':
        if score == 10:
            return random.choice(positive_feedback[:4])
        return random.choice(positive_feedback)

    elif category == 'Passive':
        return random.choice(neutral_feedback)

    else:  # Detractor
        if score <= 3:
            return random.choice(negative_feedback[:3])
        return random.choice(negative_feedback)

# -------------------------------
# Data Generation Loop
# -------------------------------
for i in range(1, num_rows + 1):

    account = random.choices(
        list(account_weights.keys()),
        weights=list(account_weights.values())
    )[0]

    vertical = accounts_verticals[account]
    client_name = fake.name()
    client_email = fake.email()
    client_designation = random.choices(designations, weights=designation_weights)[0]
    client_geo = random.choices(geographies, weights=geo_weights)[0]

    response_prob = get_response_probability(account, client_geo, client_designation)
    response_status = 'Submitted' if random.random() < response_prob else 'Did not submit'

    if response_status == 'Submitted':
        csat_rating = generate_csat(account)
        csat_cat = csat_category(csat_rating)

        # 5% noise for realism
        if random.random() < 0.05:
            feedback = random.choice(positive_feedback + neutral_feedback + negative_feedback)
        else:
            feedback = generate_feedback(csat_cat, csat_rating)

    else:
        csat_rating = None
        csat_cat = None
        feedback = None

    cursor.execute(
        "INSERT INTO CSAT VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (i, vertical, account, client_name, client_email,
         client_designation, client_geo, response_status,
         csat_rating, csat_cat, feedback)
    )

# -------------------------------
# Preview Data
# -------------------------------
print("Sample records:\n")
for row in cursor.execute("SELECT * FROM CSAT LIMIT 10"):
    print(row)

connection.commit()
connection.close()

print("\n✅ CSAT database created successfully with realistic feedback!")
