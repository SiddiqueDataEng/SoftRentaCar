"""
Page 9 – AI Chat Assistant
Public-facing chat interface for querying fleet data in natural language.
"""

import streamlit as st
import datetime
from app.style import inject_css
from app.ai_chat import chat


def render(dfs: dict):
    inject_css()

    # ── Header ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px 0;">
        <div style="font-size:3rem;">🤖</div>
        <div style="font-size:2rem;font-weight:800;color:#E63946;line-height:1.1;">Soft Rent a Car</div>
        <div style="font-size:1rem;font-weight:600;color:#c8dff0;margin-top:4px;">AI Fleet Intelligence Assistant</div>
        <div style="font-size:0.82rem;color:#5a7a96;margin-top:6px;">
            Ask anything about your fleet, revenue, drivers, or forecasts — in plain English (or Urdu 🇵🇰)
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── OpenAI key (optional) ────────────────────────────────────────
    with st.expander("⚙️ Optional: Connect GPT-4o for enhanced answers"):
        api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
        if api_key:
            import os
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("✅ GPT-4o enabled! Answers will be more nuanced.")

    st.markdown("---")

    # ── Session state for chat history ───────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = ""

    # ── Quick-prompt buttons ─────────────────────────────────────────
    st.markdown('<div style="font-size:0.82rem;color:#8eaac4;margin-bottom:8px;">💡 Quick questions:</div>', unsafe_allow_html=True)
    quick_prompts = [
        "📊 Show all KPIs",
        "💰 What's our total revenue?",
        "🚦 Driver safety summary",
        "🔴 Show active alerts",
        "🏆 Top 5 safest drivers",
        "🔧 Fleet health status",
        "📈 Revenue forecast",
        "🏙️ Busiest cities",
    ]
    btn_cols = st.columns(4)
    for i, prompt in enumerate(quick_prompts):
        with btn_cols[i % 4]:
            if st.button(prompt, key=f"qp_{i}", use_container_width=True):
                st.session_state.pending_question = prompt.split(" ", 1)[1]

    st.markdown("---")

    # ── Chat history display ─────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center;padding:30px;color:#4a6a84;">
                <div style="font-size:2rem;margin-bottom:10px;">💬</div>
                <div style="font-size:0.9rem;">Start a conversation! Ask me about revenue, drivers, forecasts, or anything fleet-related.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for turn in st.session_state.chat_history:
                # User bubble
                st.markdown(f"""
                <div style="display:flex;justify-content:flex-end;margin:8px 0;">
                    <div class="chat-user">
                        <div>{turn['user']}</div>
                        <div class="chat-timestamp">{turn['ts']} · You</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # AI bubble
                st.markdown(f"""
                <div style="display:flex;justify-content:flex-start;margin:8px 0;">
                    <div class="chat-ai">
                        <div style="font-size:0.75rem;color:#E63946;font-weight:600;margin-bottom:4px;">🤖 Soft AI</div>
                        <div>{_md_to_html(turn['ai'])}</div>
                        <div class="chat-timestamp">{turn['ts']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Input ────────────────────────────────────────────────────────
    col_in, col_btn = st.columns([6, 1])
    with col_in:
        user_input = st.text_input(
            "Ask a question …",
            value=st.session_state.pending_question,
            placeholder="e.g. What is our best performing fleet? How many accidents this year?",
            label_visibility="collapsed",
            key="chat_input",
        )
    with col_btn:
        send = st.button("Send 🚀", type="primary", use_container_width=True)

    # Clear pending
    if st.session_state.pending_question:
        st.session_state.pending_question = ""

    # ── Process input ────────────────────────────────────────────────
    if send and user_input.strip():
        with st.spinner("Thinking …"):
            response = chat(
                user_input,
                dfs,
                history=st.session_state.chat_history,
            )

        ts = datetime.datetime.now().strftime("%H:%M")
        st.session_state.chat_history.append({
            "user": user_input,
            "ai":   response,
            "ts":   ts,
        })
        st.rerun()

    # ── Clear chat ───────────────────────────────────────────────────
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", help="Clear all conversation history"):
            st.session_state.chat_history = []
            st.rerun()

    # ── Capabilities sidebar info ─────────────────────────────────────
    with st.expander("📚 What can I ask?"):
        st.markdown("""
**Revenue & Finance**
- "What's our total revenue this year?"
- "Which fleet earns the most?"
- "Show unpaid invoices"

**Operations**
- "How many trips were completed last month?"
- "What is the most popular booking type?"
- "Show busiest cities"

**Driver Safety**
- "Who are the top 5 safest drivers?"
- "How many accidents occurred?"
- "Drivers with dangerous profile"

**Fleet & Vehicles**
- "What is our fleet utilisation?"
- "Which vehicles need maintenance?"
- "Show fuel efficiency stats"

**Forecasting**
- "Forecast next month revenue"
- "Where is demand growing?"

**Alerts**
- "Show all active alerts"
- "Any expired insurance?"

*Supports English and basic Urdu queries!*
        """)


def _md_to_html(text: str) -> str:
    """Minimal markdown → HTML for chat bubbles."""
    import re
    # Bold
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    # Code
    text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)
    # Line breaks
    text = text.replace("\n", "<br>")
    # Table (basic)
    return text
