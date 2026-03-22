###############################################################################
#### CSAT APP (Text to SQL using Google Gemini pro) #########################
###############################################################################
import html
import streamlit as st
from numpy.random import randint
from app_ai import get_gemini_response, read_sql_query, prompt, greetings

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Voice of our Customers",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;600&family=Inter:wght@300;400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #f5f3ef !important;
    font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stToolbar"] { display: none; }

.block-container {
    max-width: 760px !important;
    padding: 0 1.5rem 7rem !important;
    margin: 0 auto;
}

/* Header */
.voc-header {
    text-align: center;
    padding: 2.6rem 0 1.4rem;
    border-bottom: 1.5px solid #e2ddd6;
    margin-bottom: 2rem;
}
.voc-header h1 {
    font-family: 'Lora', serif;
    font-size: 1.7rem;
    font-weight: 600;
    color: #1a1612;
    margin: 0;
}
.voc-header p {
    color: #9e9890;
    font-size: 0.84rem;
    margin: 0.35rem 0 0;
    font-weight: 300;
}

/* Chat rows */
.chat-row {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    margin-bottom: 0.6rem;
    animation: fadeUp 0.3s ease both;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.chat-row.user { flex-direction: row-reverse; }

.avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.95rem;
    flex-shrink: 0;
    margin-top: 3px;
}
.avatar.user-av { background: #2563eb; }
.avatar.bot-av  { background: #fff; border: 1.5px solid #e2ddd6; }

/* Bubbles */
.bubble {
    max-width: 80%;
    padding: 0.7rem 1rem;
    border-radius: 16px;
    font-size: 0.91rem;
    line-height: 1.55;
    word-break: break-word;
}
.bubble.user-bubble {
    background: #2563eb;
    color: #fff;
    border-bottom-right-radius: 4px;
}
.bubble.bot-bubble {
    background: #ffffff;
    color: #2c2925;
    border-bottom-left-radius: 4px;
    border: 1.5px solid #e2ddd6;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

/* SQL badge + block */
.sql-label-row {
    display: flex;
    align-items: center;
    margin: 0.65rem 0 0.25rem 0.1rem;
}
.sql-badge {
    background: #eff6ff;
    color: #2563eb;
    border: 1px solid #bfdbfe;
    border-radius: 5px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 0.15rem 0.55rem;
}
.sql-wrap {
    background: #fafaf8;
    border: 1px solid #e2ddd6;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
}
.sql-wrap pre {
    margin: 0;
    padding: 0;
    font-family: 'Courier New', Courier, monospace;
    font-size: 0.78rem;
    color: #1e3a5f;
    line-height: 1.65;
    white-space: pre-wrap;
    word-break: break-word;
    overflow: visible;
}

/* Results table */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border: 1.5px solid #e2ddd6 !important;
    overflow: hidden;
    margin-bottom: 0.6rem;
}

/* Divider */
.turn-divider { margin: 1.4rem 0; border: none; border-top: 1px dashed #e2ddd6; }

/* Empty state */
.empty-state {
    text-align: center;
    padding: 5rem 0 2rem;
    color: #c8c3bc;
}
.empty-state .icon { font-size: 2.6rem; margin-bottom: 0.6rem; }
.empty-state p { font-size: 0.88rem; }

/* Sticky input */
.input-wrap {
    position: sticky;
    bottom: 0;
    background: linear-gradient(to top, #f5f3ef 75%, transparent);
    padding: 1rem 0 0.6rem;
    z-index: 200;
}

/* Form */
[data-testid="stForm"] {
    background: #ffffff !important;
    border: 1.5px solid #d6d1cb !important;
    border-radius: 14px !important;
    padding: 0.4rem 0.7rem !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
}
[data-testid="stTextInput"] > div > div > input {
    background: transparent !important;
    color: #1a1612 !important;
    border: none !important;
    box-shadow: none !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.94rem !important;
}
[data-testid="stTextInput"] > div > div > input::placeholder { color: #bab5ae !important; }
[data-testid="stTextInput"] > label { display: none !important; }

[data-testid="stFormSubmitButton"] button {
    background: #2563eb !important;
    color: #fff !important;
    border: none !important;
    border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    padding: 0.45rem 1rem !important;
    transition: background 0.18s !important;
    white-space: nowrap;
}
[data-testid="stFormSubmitButton"] button:hover { background: #1d4ed8 !important; }

.footer {
    text-align: center;
    font-size: 0.74rem;
    color: #c8c3bc;
    padding: 0.8rem 0 0.2rem;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="voc-header">
    <h1>💬 The Voice of our Customers</h1>
    <p>Discover insights from the latest CSAT cycle. Ask anything in plain English!</p>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "conversation" not in st.session_state:
    st.session_state.conversation = []


# ── Helper: split on ; and execute every non-empty statement ──────────────────
def execute_all_queries(sql_block, db):
    """
    Split AI output on semicolons, run each statement independently,
    return list of (sql_string, dataframe) tuples.
    """
    statements = [s.strip() for s in sql_block.split(";") if s.strip()]
    return [(stmt, read_sql_query(stmt, db)) for stmt in statements]


# ── Render full conversation ──────────────────────────────────────────────────
def render_conversation():
    if not st.session_state.conversation:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">💡</div>
            <p>Type your question. I'll convert it to SQL and show the results.</p>
        </div>""", unsafe_allow_html=True)
        return

    for i, entry in enumerate(st.session_state.conversation):

        # User bubble
        q_safe = html.escape(entry["question"])
        st.markdown(f"""
        <div class="chat-row user">
            <div class="avatar user-av">🥷</div>
            <div class="bubble user-bubble">{q_safe}</div>
        </div>""", unsafe_allow_html=True)

        # Bot greeting bubble
        if entry.get("greeting"):
            g_safe = html.escape(entry["greeting"])
            st.markdown(f"""
            <div class="chat-row">
                <div class="avatar bot-av">🤖</div>
                <div class="bubble bot-bubble">{g_safe}</div>
            </div>""", unsafe_allow_html=True)

        # Each SQL statement + its result table
        queries = entry.get("queries", [])
        multi = len(queries) > 1

        for idx, (stmt, df) in enumerate(queries):
            # Badge label: "Query 1 of 2" when multiple, plain label when single
            label = f"⚡ Query {idx + 1} of {len(queries)}" if multi else "⚡ Generated SQL"
            sql_safe = html.escape(stmt)
            st.markdown(f"""
            <div class="sql-label-row">
                <span class="sql-badge">{label}</span>
            </div>
            <div class="sql-wrap"><pre>{sql_safe}</pre></div>
            """, unsafe_allow_html=True)

            if df.empty:
                st.info("No results found for this query.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

        # Dashed divider between conversation turns
        if i < len(st.session_state.conversation) - 1:
            st.markdown('<hr class="turn-divider">', unsafe_allow_html=True)


render_conversation()

# ── Sticky input form ─────────────────────────────────────────────────────────
st.markdown("<div class='input-wrap'>", unsafe_allow_html=True)
with st.form(key="question_form", clear_on_submit=True):
    col_inp, col_btn = st.columns([0.83, 0.17])
    with col_inp:
        question = st.text_input(
            "question",
            placeholder="e.g. What is the average CSAT score this month?",
            label_visibility="collapsed",
        )
    with col_btn:
        submit = st.form_submit_button("Send ➤")
st.markdown("</div>", unsafe_allow_html=True)

# ── Process new question ──────────────────────────────────────────────────────
if submit and question.strip():
    greeting = greetings[randint(0, len(greetings) - 1)]
    with st.spinner("Thinking... generating SQL and fetching results ⚙️"):
        sql_block = get_gemini_response(question, prompt)
        queries = execute_all_queries(sql_block, "csat.db")
    st.session_state.conversation.append({
        "question": question,
        "greeting": greeting,
        "queries": queries,
    })
    st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div class='footer'>Made with ❤️ by <strong>CHHETRI</strong></div>", unsafe_allow_html=True)