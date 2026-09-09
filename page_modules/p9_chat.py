"""AI Chat Assistant — with inline charts & tables"""
import streamlit as st
import datetime
import os
import re
import pandas as pd
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE,
    TEXT, GRID, BG, COLORS, dark_layout,
)

inject()
dfs = get_data()

# ── CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.chat-hero {
    background: linear-gradient(135deg,#0f1e30 0%,#1a0a14 50%,#0f1e30 100%);
    border:1px solid #2d1f2e; border-radius:20px;
    padding:26px 22px 18px; text-align:center; margin-bottom:14px;
    position:relative; overflow:hidden;
}
.chat-hero::before {
    content:''; position:absolute; inset:0;
    background:radial-gradient(ellipse at 50% 0%,rgba(230,57,70,.18) 0%,transparent 65%);
    pointer-events:none;
}
.chat-hero-icon  { font-size:2.6rem; line-height:1; }
.chat-hero-title { font-size:1.7rem; font-weight:800; color:#E63946; margin-top:5px; }
.chat-hero-sub   { font-size:.88rem; color:#c8dff0; margin-top:2px; font-weight:500; }
.chat-hero-desc  { font-size:.74rem; color:#5a7a96; margin-top:4px; }
.gpt-badge     { display:inline-block; background:linear-gradient(90deg,#10a37f,#1a7f5a);
                 color:#fff; font-size:.65rem; font-weight:700; padding:3px 10px;
                 border-radius:20px; letter-spacing:.06em; margin-top:7px; text-transform:uppercase; }
.gpt-badge-off { display:inline-block; background:rgba(90,122,150,.25); color:#8eaac4;
                 font-size:.65rem; font-weight:600; padding:3px 10px; border-radius:20px;
                 letter-spacing:.06em; margin-top:7px; text-transform:uppercase; border:1px solid #2d4a6b; }
.status-bar { display:flex; align-items:center; gap:8px;
              font-size:.7rem; color:#5a7a96; margin-bottom:8px; }
.sdot-g { width:7px;height:7px;background:#2A9D8F;border-radius:50%;flex-shrink:0; }
.sdot-r { width:7px;height:7px;background:#3a5a74;border-radius:50%;flex-shrink:0; }

/* ── Message bubbles ── */
.msg-user-wrap { display:flex; justify-content:flex-end; margin:10px 0 4px; }
.bubble-user {
    background:linear-gradient(135deg,#E63946,#b02030); color:#fff;
    padding:10px 15px; border-radius:18px 18px 4px 18px; max-width:68%;
    font-size:.87rem; line-height:1.5; box-shadow:0 4px 14px rgba(230,57,70,.22);
}
.bubble-user-ts { font-size:.63rem; color:rgba(255,255,255,.38); text-align:right; margin-top:3px; }

.msg-ai-wrap  { display:flex; align-items:flex-start; gap:9px; margin:4px 0 6px; }
.ai-avatar {
    width:30px; height:30px; background:linear-gradient(135deg,#E63946,#8b0000);
    border-radius:50%; display:flex; align-items:center; justify-content:center;
    font-size:.9rem; flex-shrink:0; box-shadow:0 2px 8px rgba(230,57,70,.32);
    margin-top:2px;
}
.bubble-ai {
    background:linear-gradient(135deg,#1a2840,#1e3248); color:#d8eaf6;
    padding:12px 15px; border-radius:4px 18px 18px 18px; max-width:86%;
    font-size:.87rem; line-height:1.6; border:1px solid #253d58;
    box-shadow:0 2px 10px rgba(0,0,0,.28);
}
.ai-label  { font-size:.64rem; color:#E63946; font-weight:700; margin-bottom:3px; letter-spacing:.04em; }
.ai-ts     { font-size:.62rem; color:#3a5a74; margin-top:4px; }
.src-gpt  { font-size:.62rem; color:#10a37f; background:rgba(16,163,127,.12);
             padding:2px 7px; border-radius:8px; display:inline-block; margin-top:3px;
             border:1px solid rgba(16,163,127,.25); }
.src-rule { font-size:.62rem; color:#5a7a96; background:rgba(90,122,150,.1);
             padding:2px 7px; border-radius:8px; display:inline-block; margin-top:3px;
             border:1px solid #253d58; }

/* ── Visual card ── */
.visual-card {
    background:linear-gradient(135deg,#111e2c,#14202e);
    border:1px solid #1e3044; border-radius:14px;
    padding:14px 16px; margin:8px 0 12px 39px;
}
.visual-insight {
    font-size:.74rem; color:#5a7a96; margin-top:6px;
    border-top:1px solid #1e3044; padding-top:6px;
}

.empty-state { text-align:center; padding:36px 20px; color:#3a5a74; }
.empty-icon  { font-size:2rem; margin-bottom:8px; opacity:.3; }
</style>
""", unsafe_allow_html=True)

# ── Key ────────────────────────────────────────────────────────────────
from app.ai_chat import _resolve_key
api_key_active = bool(_resolve_key())

if not api_key_active:
    with st.sidebar:
        st.markdown("---")
        st.markdown('<div style="font-size:.73rem;color:#8eaac4;margin-bottom:3px;">🔑 OpenAI Key</div>',
                    unsafe_allow_html=True)
        uk = st.text_input("Key", type="password", key="chat_api_key",
                           placeholder="sk-...", label_visibility="collapsed")
        if uk and len(uk) > 20:
            os.environ["OPENAI_API_KEY"] = uk
            api_key_active = True
            st.success("GPT-4o ✓")

# ── Session ────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # list of {user, ai, visual, ts}

# ── Hero ───────────────────────────────────────────────────────────────
badge = ('<span class="gpt-badge">✦ GPT-4o Active</span>' if api_key_active
         else '<span class="gpt-badge-off">⚡ Rule-based Mode</span>')
st.markdown(f"""
<div class="chat-hero">
  <div class="chat-hero-icon">🤖</div>
  <div class="chat-hero-title">Soft Rent a Car AI</div>
  <div class="chat-hero-sub">Fleet Intelligence Assistant</div>
  <div class="chat-hero-desc">Ask anything — charts and tables appear automatically for analytical questions</div>
  {badge}
</div>""", unsafe_allow_html=True)

dot = "sdot-g" if api_key_active else "sdot-r"
eng = "GPT-4o" if api_key_active else "Rule-based"
st.markdown(f"""
<div class="status-bar">
  <div class="{dot}"></div>
  <span>{eng} · {len(dfs['trips']):,} trips · PKR {dfs['invoices']['total_amount_pkr'].sum()/1e6:.1f}M revenue · {len(dfs['vehicles'])} vehicles</span>
</div>""", unsafe_allow_html=True)

# ── Quick prompts ──────────────────────────────────────────────────────
QUICK = [
    ("📊 All KPIs",          "Show all KPIs"),
    ("💰 Revenue Trend",     "Show monthly revenue trend"),
    ("🚗 Top 10 Cars",       "Top 10 vehicles by revenue"),
    ("📅 Month vs Last",     "Compare current month vs last month revenue"),
    ("📆 YoY Same Month",    "Compare this month vs same month last year"),
    ("🏙️ City Demand",      "Show trip demand and revenue by city"),
    ("🚦 Driver Safety",     "Driver safety score summary"),
    ("🏆 Top Drivers",       "Top 10 safest drivers"),
    ("⚠️ Risky Drivers",    "Show worst 10 drivers who need coaching"),
    ("⛽ Fuel Efficiency",   "Fuel efficiency and cost trend"),
    ("🔧 Maintenance",       "Maintenance cost by type"),
    ("👥 Customers",         "Customer segment revenue breakdown"),
]

st.markdown('<div style="font-size:.72rem;color:#8eaac4;margin-bottom:5px;">⚡ Quick questions — charts appear automatically</div>',
            unsafe_allow_html=True)
bc = st.columns(6)
for i, (label, q) in enumerate(QUICK):
    if bc[i % 6].button(label, key=f"qp_{i}", width='stretch'):
        with st.spinner("Analysing …"):
            from app.visual_chat import chat_with_visual
            text, visual = chat_with_visual(q, dfs, history=st.session_state.chat_history)
        ts = datetime.datetime.now().strftime("%H:%M")
        st.session_state.chat_history.append(
            {"user": q, "ai": text, "visual": visual, "ts": ts}
        )
        st.rerun()

st.markdown("<hr style='border-color:#1e2f44;margin:10px 0'>", unsafe_allow_html=True)

# ── Markdown renderer ──────────────────────────────────────────────────
def _md(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"### (.*?)(\n|$)",
                  r"<div style='font-weight:700;color:#c8dff0;margin:5px 0 2px;font-size:.91rem;'>\1</div>", text)
    text = re.sub(r"## (.*?)(\n|$)",
                  r"<div style='font-size:.98rem;font-weight:800;color:#E63946;margin:6px 0 2px;'>\1</div>", text)
    text = re.sub(r"`(.*?)`",
                  r"<code style='background:#0f1a24;padding:1px 5px;border-radius:4px;"
                  r"font-size:.81rem;color:#7dd8cc;'>\1</code>", text)
    lines = []
    in_table = False
    for line in text.split("\n"):
        if "|" in line and "---" not in line:
            if not in_table:
                lines.append(
                    '<table style="border-collapse:collapse;width:100%;font-size:.81rem;margin:5px 0;">'
                )
                in_table = True
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            s = "padding:4px 8px;border:1px solid #253d58;color:#c8dff0;"
            lines.append("<tr>" + "".join(f"<td style='{s}'>{c}</td>" for c in cells) + "</tr>")
        else:
            if in_table:
                lines.append("</table>")
                in_table = False
            if line.startswith("- ") or line.startswith("• "):
                lines.append(f"<li style='margin:2px 0;color:#c8dff0;'>{line[2:]}</li>")
            else:
                lines.append(line)
    if in_table:
        lines.append("</table>")
    return "<br>".join(lines)


# ── Visual renderer ────────────────────────────────────────────────────
def _render_visual(visual: dict, key_suffix: str):
    """Render chart + table inside a visual card below the AI bubble."""
    if not visual:
        return

    vtype   = visual.get("type", "bar")
    title   = visual.get("title", "")
    df      = visual.get("df")
    x_col   = visual.get("x", "")
    y_col   = visual.get("y", "")
    fmt_pkr = visual.get("fmt_pkr", [])
    insight = visual.get("insight", "")

    if df is None or df.empty:
        return

    st.markdown('<div class="visual-card">', unsafe_allow_html=True)

    # ── Build figure ──────────────────────────────────────────────────
    fig = None

    if vtype == "kpi_table":
        # Pure table — no chart
        st.markdown(
            f'<div style="font-size:.78rem;font-weight:700;color:#c8dff0;margin-bottom:6px;">{title}</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(df, width='stretch', hide_index=True, height=320)

    elif vtype == "horizontal_bar":
        y_vals = df[y_col].tolist()
        x_vals = df[x_col].tolist()
        fig = go.Figure(go.Bar(
            x=x_vals, y=y_vals, orientation="h",
            marker=dict(
                color=x_vals,
                colorscale=[[0, NAVY], [0.5, STEEL], [1, BRAND]],
                showscale=False,
            ),
            text=[f"{v:,.0f}" if c in fmt_pkr else str(v) for v, c in zip(x_vals, [x_col]*len(x_vals))],
            textposition="outside",
            textfont=dict(color=TEXT, size=9),
        ))
        dark_layout(fig, title, height=max(260, len(y_vals) * 26 + 60))
        fig.update_yaxes(autorange="reversed")

    elif vtype == "grouped_bar":
        y_list = y_col if isinstance(y_col, list) else [y_col]
        fig = go.Figure()
        for i, yc in enumerate(y_list):
            fig.add_trace(go.Bar(
                name=yc.replace("_", " ").title(),
                x=df[x_col],
                y=df[yc],
                marker_color=COLORS[i % len(COLORS)],
                opacity=0.88,
            ))
        fig.update_layout(barmode="group")
        dark_layout(fig, title, height=340, xangle=-30)

    elif vtype == "area":
        y_list = y_col if isinstance(y_col, list) else [y_col]
        fig = go.Figure()
        for i, yc in enumerate(y_list):
            fig.add_trace(go.Scatter(
                x=df[x_col], y=df[yc],
                name=yc.replace("_", " ").title(),
                mode="lines+markers",
                fill="tozeroy" if i == 0 else "tonexty",
                fillcolor=f"rgba({[230,69,42,230][i%4]},{[57,123,157,57][i%4]},{[70,157,70,70][i%4]},.15)",
                line=dict(color=COLORS[i % len(COLORS)], width=2.2),
                marker=dict(size=4),
            ))
        dark_layout(fig, title, height=320, xangle=-35)

    elif vtype == "bar":
        y_list = y_col if isinstance(y_col, list) else [y_col]
        fig = go.Figure()
        for i, yc in enumerate(y_list):
            fig.add_trace(go.Bar(
                name=yc.replace("_", " ").title(),
                x=df[x_col], y=df[yc],
                marker_color=COLORS[i % len(COLORS)],
                opacity=0.88,
            ))
        dark_layout(fig, title, height=320, xangle=-20)

    elif vtype == "pie":
        fig = go.Figure(go.Pie(
            labels=df[x_col], values=df[y_col if isinstance(y_col, str) else y_col[0]],
            hole=0.5,
            marker=dict(colors=COLORS, line=dict(color="#0f1117", width=2)),
            textfont=dict(color="#fff", size=10),
        ))
        dark_layout(fig, title, height=300)

    if fig:
        st.plotly_chart(fig, width='stretch', key=f"vc_{key_suffix}")

    # ── Data table (collapsible) ───────────────────────────────────────
    with st.expander("📋 View data table", expanded=False):
        display_df = df.copy()
        for col in fmt_pkr:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda v: f"PKR {float(v)/1e6:.2f}M" if float(v) >= 1e6
                    else (f"PKR {float(v)/1e3:.1f}K" if float(v) >= 1e3
                          else f"PKR {float(v):,.0f}")
                )
        st.dataframe(display_df, width='stretch', hide_index=True)

    # ── Insight bar ────────────────────────────────────────────────────
    if insight:
        st.markdown(f'<div class="visual-insight">💡 {insight}</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── Chat display ───────────────────────────────────────────────────────
src_badge = ('<span class="src-gpt">GPT-4o</span>' if api_key_active
             else '<span class="src-rule">Analytics Engine</span>')

if not st.session_state.chat_history:
    st.markdown("""
<div style="background:linear-gradient(180deg,#0a1520,#0d1a28);border:1px solid #1e2f44;
            border-radius:16px;padding:16px;min-height:160px;margin-bottom:12px;">
  <div class="empty-state">
    <div class="empty-icon">💬</div>
    <div style="font-size:.88rem;font-weight:500;color:#3a5a74;">Start a conversation</div>
    <div style="font-size:.75rem;color:#2a4a64;margin-top:4px;">
      Click a quick question above or type below — charts appear automatically
    </div>
  </div>
</div>""", unsafe_allow_html=True)
else:
    for idx, turn in enumerate(st.session_state.chat_history):
        # User bubble
        st.markdown(f"""
<div class="msg-user-wrap">
  <div>
    <div class="bubble-user">{turn['user']}</div>
    <div class="bubble-user-ts">{turn['ts']} · You</div>
  </div>
</div>""", unsafe_allow_html=True)

        # AI bubble
        st.markdown(f"""
<div class="msg-ai-wrap">
  <div class="ai-avatar">🤖</div>
  <div style="flex:1;min-width:0;">
    <div class="ai-label">SOFT AI</div>
    <div class="bubble-ai">{_md(turn['ai'])}{src_badge}</div>
    <div class="ai-ts">{turn['ts']}</div>
  </div>
</div>""", unsafe_allow_html=True)

        # Visual (chart + table) if present
        visual = turn.get("visual")
        if visual:
            _render_visual(visual, key_suffix=f"{idx}_{turn['ts'].replace(':','')}")

# ── Input form ─────────────────────────────────────────────────────────
with st.form(key="chat_form", clear_on_submit=True):
    ic, bc2 = st.columns([7, 1])
    user_input = ic.text_input(
        "msg",
        placeholder="Ask anything — 'top 5 cars', 'compare last month vs current', 'city demand chart' …",
        label_visibility="collapsed",
        key="chat_input_field",
    )
    send = bc2.form_submit_button("Send ▶", width='stretch')

if send and user_input.strip():
    with st.spinner("Analysing …"):
        from app.visual_chat import chat_with_visual
        text, visual = chat_with_visual(
            user_input.strip(), dfs,
            history=st.session_state.chat_history,
        )
    ts = datetime.datetime.now().strftime("%H:%M")
    st.session_state.chat_history.append(
        {"user": user_input.strip(), "ai": text, "visual": visual, "ts": ts}
    )
    st.rerun()

# ── Footer ─────────────────────────────────────────────────────────────
if st.session_state.chat_history:
    f1, f2, _ = st.columns([1, 1, 5])
    if f1.button("🗑️ Clear", key="chat_clear", width='stretch'):
        st.session_state.chat_history = []
        st.rerun()
    if f2.button("📋 Export", key="chat_export", width='stretch'):
        import json
        safe = [{k: v for k, v in t.items() if k != "visual"}
                for t in st.session_state.chat_history]
        st.download_button("⬇ JSON", json.dumps(safe, indent=2),
                           "chat.json", "application/json", key="chat_dl")

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown('<div style="font-size:.76rem;font-weight:700;color:#c8dff0;margin-bottom:5px;">📊 Questions with auto-charts</div>',
                unsafe_allow_html=True)
    st.markdown("""
<div style="font-size:.7rem;color:#4a6a84;line-height:1.85;">
🚗 Top N vehicles by revenue<br>
📅 Current month revenue<br>
📆 Month vs month comparison<br>
📆 Year-over-year same month<br>
📈 Monthly revenue trend<br>
🏙️ City demand &amp; revenue<br>
🚦 Driver safety scores<br>
🏆 Top / worst drivers<br>
⛽ Fuel efficiency trend<br>
🔧 Maintenance by type<br>
👥 Customer segments<br>
💳 Payment methods<br>
📊 All KPIs table<br>
🚗 Fleet utilisation<br>
🚘 Fleet revenue split
</div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div style="font-size:.7rem;color:#3a5a74;">💡 All other questions get text answers via GPT-4o</div>',
                unsafe_allow_html=True)

