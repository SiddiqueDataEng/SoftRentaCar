"""AI Chat Assistant"""
import streamlit as st
import datetime
from page_modules._shared import inject, get_data, BRAND, STEEL, TEXT

inject()
dfs = get_data()

st.markdown(f"""
<div style="text-align:center;padding:16px 0 8px 0;">
  <div style="font-size:2.5rem;">🤖</div>
  <div style="font-size:1.8rem;font-weight:800;color:{BRAND};line-height:1.1;">Soft Rent a Car</div>
  <div style="font-size:.95rem;font-weight:600;color:#c8dff0;margin-top:3px;">AI Fleet Intelligence Assistant</div>
  <div style="font-size:.78rem;color:#5a7a96;margin-top:4px;">
    Ask anything about your fleet, revenue, drivers or forecasts — in plain English
  </div>
</div>
<hr style="border-color:#1e2f44;margin:8px 0 14px 0">
""", unsafe_allow_html=True)

# Optional GPT-4o key
with st.expander("⚙️ Optional: Connect GPT-4o for enhanced answers"):
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    if api_key:
        import os; os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ GPT-4o enabled!")

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_q" not in st.session_state:
    st.session_state.pending_q = ""

# Quick prompts
st.markdown(f'<div style="font-size:.78rem;color:#8eaac4;margin-bottom:6px;">💡 Quick questions:</div>', unsafe_allow_html=True)
prompts = [
    ("📊 All KPIs",           "Show all KPIs"),
    ("💰 Total Revenue",      "What is our total revenue?"),
    ("🚦 Driver Safety",      "Driver safety summary"),
    ("🔴 Active Alerts",      "Show active alerts"),
    ("🏆 Top Drivers",        "Top 5 safest drivers"),
    ("🔧 Fleet Health",       "Fleet health status"),
    ("🏙️ Busiest Cities",     "Show busiest cities"),
    ("👥 Customers",          "Customer breakdown"),
]
bcols = st.columns(4)
for i, (label, q) in enumerate(prompts):
    if bcols[i%4].button(label, key=f"qp{i}", use_container_width=True):
        st.session_state.pending_q = q
        st.rerun()

st.markdown("<hr style='border-color:#1e2f44;margin:8px 0'>", unsafe_allow_html=True)

# Chat history
if not st.session_state.chat_history:
    st.markdown(f"""
<div style="text-align:center;padding:26px;color:#4a6a84;">
  <div style="font-size:1.8rem;margin-bottom:8px;">💬</div>
  <div style="font-size:.88rem;">Start a conversation! Ask about revenue, drivers, forecasts, or any fleet metric.</div>
</div>""", unsafe_allow_html=True)
else:
    for turn in st.session_state.chat_history:
        st.markdown(f"""
<div style="display:flex;justify-content:flex-end;margin:6px 0;">
  <div class="chat-user">
    <div>{turn['user']}</div>
    <div class="chat-ts">{turn['ts']} · You</div>
  </div>
</div>
<div style="display:flex;justify-content:flex-start;margin:6px 0;">
  <div class="chat-ai">
    <div style="font-size:.72rem;color:{BRAND};font-weight:700;margin-bottom:3px;">🤖 Soft AI</div>
    <div>{_md(turn['ai'])}</div>
    <div class="chat-ts">{turn['ts']}</div>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown("<hr style='border-color:#1e2f44;margin:8px 0'>", unsafe_allow_html=True)

# Input row
ci, cb = st.columns([6,1])
user_input = ci.text_input("Ask …", value=st.session_state.pending_q,
    placeholder="e.g. What is our best fleet? How many accidents this year?",
    label_visibility="collapsed", key="chat_in")
send = cb.button("Send 🚀", type="primary", use_container_width=True)

if st.session_state.pending_q:
    st.session_state.pending_q = ""

if send and user_input.strip():
    with st.spinner("Thinking …"):
        from app.ai_chat import chat
        response = chat(user_input, dfs, history=st.session_state.chat_history)
    ts = datetime.datetime.now().strftime("%H:%M")
    st.session_state.chat_history.append({"user": user_input, "ai": response, "ts": ts})
    st.rerun()

if st.session_state.chat_history:
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

with st.expander("📚 What can I ask?"):
    st.markdown("""
**Revenue:** total revenue, best fleet, payment methods  
**Trips:** completed trips, cancellations, popular routes  
**Drivers:** safety scores, accidents, top performers  
**Fleet:** utilisation, maintenance due, fuel efficiency  
**Alerts:** expired insurance, overdue invoices, risky drivers  
**Forecasting:** revenue outlook, demand by city  
**KPIs:** collection rate, avg fare, trip completion rate  
""")


def _md(text: str) -> str:
    import re
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)
    return text.replace("\n", "<br>")
