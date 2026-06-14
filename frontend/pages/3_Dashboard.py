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
selected_case_title = st.selectbox("Select Case", options=list(case_options.keys()))
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
            "risk_level": analysis.get("risk_level", "none"),
            "risk_score": analysis.get("risk_score", 0.0),
            "categories": analysis.get("categories", []),
            "author": msg.get("author_alias") or "Unknown"
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
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.success("No problematic patterns detected in this case.")

st.divider()

# ── Risk level distribution ───────────────────────────────────────────────────
st.subheader("Risk Level Distribution")

risk_counts = df['risk_level'].value_counts().reset_index()
risk_counts.columns = ["Risk Level", "Count"]

color_map = {
    "none": "#2d6a4f",
    "low": "#b5850a",
    "medium": "#b84c00",
    "high": "#9b2226"
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

# ── Message table ─────────────────────────────────────────────────────────────
st.subheader("Message Details")
display_df = df[["date_fmt", "author", "message", "risk_level", "risk_score"]].copy()
display_df.columns = ["Date", "Author", "Message", "Risk Level", "Risk Score"]
st.dataframe(display_df, use_container_width=True, hide_index=True)