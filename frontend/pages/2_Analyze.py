# Analyze page — Add messages to a case and run AI analysis.

import streamlit as st
import requests
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

def create_message(case_id: int, content: str, author_alias: str):
    response = requests.post(
        f"{API_URL}/cases/{case_id}/messages/",
        json={"content": content, "author_alias": author_alias or None},
        headers=headers
    )
    return response.json() if response.status_code == 201 else None

def analyze_message(case_id: int, message_id: int):
    response = requests.post(
        f"{API_URL}/cases/{case_id}/messages/{message_id}/analyze",
        headers=headers
    )
    return response.json() if response.status_code == 201 else None

def get_analysis(case_id: int, message_id: int):
    response = requests.get(
        f"{API_URL}/cases/{case_id}/messages/{message_id}",
        headers=headers
    )
    if response.status_code == 200:
        msg = response.json()
        analysis_response = requests.get(
            f"{API_URL}/cases/{case_id}/messages/{message_id}/analysis",
            headers=headers
        )
        return analysis_response.json() if analysis_response.status_code == 200 else None
    return None

# ── Risk level styling ────────────────────────────────────────────────────────
def risk_badge(level: str) -> str:
    colors = {
        "none": ("🟢", "#2d6a4f"),
        "low": ("🟡", "#b5850a"),
        "medium": ("🟠", "#b84c00"),
        "high": ("🔴", "#9b2226")
    }
    emoji, color = colors.get(level, ("⚪", "#888888"))
    return f'<span style="font-size:0.85rem; color:{color}; font-weight:600;">{emoji} {level.capitalize()} risk</span>'

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🔍 Analyze Messages")
st.divider()

cases = get_cases()
if not cases:
    st.info("No cases found. Please create a case first.")
    st.page_link("pages/1_Cases.py", label="➕ Go to Cases")
    st.stop()

# Case selector
case_options = {f"{c['title']}": c['id'] for c in cases}
selected_case_title = st.selectbox("Select Case", options=list(case_options.keys()))
selected_case_id = case_options[selected_case_title]

st.divider()

# Add new message
with st.expander("➕ Add New Message", expanded=True):
    with st.form("add_message_form"):
        content = st.text_area(
            "Message Content",
            placeholder="Paste the message you want to analyze...",
            max_chars=2000,
            height=120
        )
        author_alias = st.text_input(
            "Author Alias (optional)",
            placeholder="e.g. Person A, Colleague",
            max_chars=50
        )
        st.caption("⚠️ For privacy reasons, avoid using real names.")
        submitted = st.form_submit_button("Add & Analyze", use_container_width=True)

        if submitted:
            if content:
                with st.spinner("Adding message..."):
                    message = create_message(selected_case_id, content, author_alias)
                if message:
                    with st.spinner("Analyzing message... this may take a moment."):
                        analysis = analyze_message(selected_case_id, message["id"])
                    if analysis:
                        st.rerun()
                    else:
                        st.error("Analysis failed. Please try again.")
                else:
                    st.error("Failed to add message.")
            else:
                st.warning("Please enter a message.")

st.divider()

# Message list with analysis
st.subheader("Messages in this Case")
messages = get_messages(selected_case_id)

if not messages:
    st.info("No messages yet. Add your first message above.")
else:
    for msg in reversed(messages):
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{msg.get('author_alias') or 'Unknown'}**")
                st.write(msg['content'])
                date_parts = msg['timestamp'][:10].split("-")
                st.caption(f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}")
            with col2:
                # Check if analysis exists
                analysis_resp = requests.get(
                    f"{API_URL}/cases/{selected_case_id}/messages/{msg['id']}/analysis",
                    headers=headers
                )
                if analysis_resp.status_code == 200:
                    analysis = analysis_resp.json()
                    level = analysis.get("risk_level", "none")
                    st.markdown(risk_badge(level), unsafe_allow_html=True)
                else:
                    if st.button("Analyze", key=f"analyze_{msg['id']}"):
                        with st.spinner("Analyzing..."):
                            analyze_message(selected_case_id, msg['id'])
                        st.rerun()

        # Show analysis details
        if analysis_resp.status_code == 200:
            analysis = analysis_resp.json()
            if analysis.get("risk_level") != "none":
                with st.expander("📋 View Analysis", expanded=False):
                    st.markdown("**Explanation**")
                    st.info(analysis.get("explanation", ""))

                    st.markdown("**Response Strategies**")
                    strategies = analysis.get("response_strategies", [])
                    if strategies:
                        tabs = st.tabs([s["type"] for s in strategies])
                        for tab, strategy in zip(tabs, strategies):
                            with tab:
                                st.write(strategy["example"])
                                st.caption(strategy["description"])
            else:
                with st.expander("📋 View Analysis", expanded=False):
                    st.success(analysis.get("explanation", "This message does not contain problematic communication patterns."))