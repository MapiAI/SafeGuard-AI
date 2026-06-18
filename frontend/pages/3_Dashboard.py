# Dashboard page — Behavioral pattern timeline and analytics for a case.

import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
sys.path.append("..")
from components import show_sidebar, check_auth

API_URL = "http://127.0.0.1:8000"

# ── Auth check ────────────────────────────────────────────────────────────────
if not st.session_state.get("token"):
    st.warning("Please login to access this page.")
    st.stop()

token = st.session_state.token
headers = {"Authorization": f"Bearer {token}"}

show_sidebar()
check_auth(headers)

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_cases():
    response = requests.get(f"{API_URL}/cases/", headers=headers)
    return response.json() if response.status_code == 200 else []

def get_messages(case_id: int):
    response = requests.get(f"{API_URL}/cases/{case_id}/messages/", headers=headers)
    return response.json() if response.status_code == 200 else []

def get_analysis(case_id: int, message_id: int):
    response = requests.get(
        f"{API_URL}/cases/{case_id}/messages/{message_id}/analysis",
        headers=headers
    )
    return response.json() if response.status_code == 200 else None

def format_date(date_str: str) -> str:
    parts = date_str[:10].split("-")
    return f"{parts[2]}-{parts[1]}-{parts[0]}"

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("📊 Dashboard")
st.caption("Behavioral pattern analysis and communication trends over time.")
st.divider()

cases = get_cases()
if not cases:
    st.info("No cases found. Please create a case first.")
    st.stop()

# Case selector
case_options = {c['title']: c['id'] for c in cases}
# Case selector — use preselected case if coming from Cases page
preselected = st.session_state.get("selected_case_id", None)
default_index = 0
if preselected:
    ids = [c['id'] for c in cases]
    if preselected in ids:
        default_index = ids.index(preselected)
    st.session_state.selected_case_id = None  # reset after use

selected_case_title = st.selectbox(
    "Select Case",
    options=list(case_options.keys()),
    index=default_index
)
selected_case_id = case_options[selected_case_title]

st.divider()

# Load data
messages = get_messages(selected_case_id)
if not messages:
    st.info("No messages in this case yet.")
    st.stop()

# Build dataframe
rows = []
for msg in messages:
    analysis = get_analysis(selected_case_id, msg['id'])
    if analysis:
        rows.append({
            "date": msg['timestamp'][:10],
            "date_fmt": format_date(msg['timestamp']),
            "message": msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content'],
            "full_message": msg['content'],  
            "risk_level": analysis.get("risk_level", "none"),
            "risk_score": analysis.get("risk_score", 0.0),
            "categories": analysis.get("categories", []),
            "author": msg.get("author_alias") or "Unknown",
            "msg_id": msg['id']  #
        })

if not rows:
    st.info("No analyses found. Analyze some messages first.")
    st.stop()

df = pd.DataFrame(rows)
df = df.sort_values("date")

# ── Summary metrics ───────────────────────────────────────────────────────────
st.subheader("Summary")
col1, col2, col3, col4 = st.columns(4)

total = len(df)
high = len(df[df['risk_level'] == 'high'])
medium = len(df[df['risk_level'] == 'medium'])
none_low = len(df[df['risk_level'].isin(['none', 'low'])])

with col1:
    st.metric("Total Messages", total)
with col2:
    st.metric("🔴 High Risk", high)
with col3:
    st.metric("🟠 Medium Risk", medium)
with col4:
    st.metric("🟢 None / Low", none_low)

st.divider()

# ── Risk score timeline ───────────────────────────────────────────────────────
st.subheader("Risk Score Over Time")

fig_timeline = px.line(
    df,
    x="date_fmt",
    y="risk_score",
    markers=True,
    color_discrete_sequence=["#e63946"],
    labels={"date_fmt": "Date", "risk_score": "Risk Score"},
)
fig_timeline.update_layout(
    yaxis_range=[0, 1],
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Date",
    yaxis_title="Risk Score"
)
fig_timeline.add_hrect(y0=0.7, y1=1.0, fillcolor="red", opacity=0.05, line_width=0)
fig_timeline.add_hrect(y0=0.5, y1=0.7, fillcolor="orange", opacity=0.05, line_width=0)
st.plotly_chart(fig_timeline, use_container_width=True)

st.divider()

# ── Category distribution ─────────────────────────────────────────────────────
st.subheader("Detected Pattern Distribution")

category_counts = {}
for _, row in df.iterrows():
    for cat in row['categories']:
        name = cat['category']
        category_counts[name] = category_counts.get(name, 0) + 1

if category_counts:
    cat_df = pd.DataFrame(
        list(category_counts.items()),
        columns=["Category", "Count"]
    ).sort_values("Count", ascending=True)

    fig_bar = px.bar(
    cat_df,
    x="Count",
    y="Category",
    orientation="h",
    color="Count",
    color_continuous_scale="Reds",
    labels={"Count": "Occurrences", "Category": "Pattern"}
    )
    
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        coloraxis_showscale=False
    )
    
    fig_bar.update_xaxes(
        dtick=1,
        tick0=0,
        tickformat="d"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.success("No problematic patterns detected in this case.")

st.divider()

# ── Risk level distribution ───────────────────────────────────────────────────
st.subheader("Risk Level Distribution")

risk_counts = df['risk_level'].value_counts().reset_index()
risk_counts.columns = ["Risk Level", "Count"]

color_map = {
    "none": "#9ed7a0",
    "low": "#f7efa2",
    "medium": "#fdbc5a",
    "high": "#dd5c5c"
}

fig_pie = px.pie(
    risk_counts,
    names="Risk Level",
    values="Count",
    color="Risk Level",
    color_discrete_map=color_map
)
fig_pie.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# Risk badge
def risk_badge(level: str) -> str:
    colors = {
        "none": ("🟢", "#2d6a4f"),
        "low": ("🟡", "#b5850a"),
        "medium": ("🟠", "#b84c00"),
        "high": ("🔴", "#9b2226")
    }
    emoji, color = colors.get(level, ("⚪", "#888888"))
    return f'<span style="font-size:0.85rem; color:{color}; font-weight:600;">{emoji} {level.capitalize()} risk</span>'

# ── Message table ─────────────────────────────────────────────────────────────
st.subheader("Message Details")

for _, row in df.iterrows():
    with st.expander(f"{row['date_fmt']} — {row['author']} — {row['risk_level'].upper()}"):
        st.write(row['full_message'])
        
        # Find full analysis
        msg_id = row.get('msg_id')
        if msg_id:
            analysis_resp = requests.get(
                f"{API_URL}/cases/{selected_case_id}/messages/{msg_id}/analysis",
                headers=headers
            )
            if analysis_resp.status_code == 200:
                analysis = analysis_resp.json()
                
                # Risk badge
                risk_level = analysis.get("risk_level", "none")
                st.markdown(risk_badge(risk_level), unsafe_allow_html=True)
            
                # Explanation
                if analysis.get("explanation"):
                    st.markdown("**Explanation**")
                    st.info(analysis.get("explanation"))
                    if analysis.get("context_note"):
                        st.caption(f"ℹ️ {analysis.get('context_note')}")
                
                # Response strategies
                strategies = analysis.get("response_strategies", [])
                if strategies and risk_level != "none":
                    st.markdown("**Response Strategies**")
                    tabs = st.tabs([s["type"] for s in strategies])
                    for tab, strategy in zip(tabs, strategies):
                        with tab:
                            st.write(strategy["example"])
                            st.caption(strategy["description"])