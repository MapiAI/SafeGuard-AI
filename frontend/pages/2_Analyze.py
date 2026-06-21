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

def create_message(case_id: int, content: str):
    response = requests.post(
        f"{API_URL}/cases/{case_id}/messages/",
        json={"content": content},
        headers=headers
    )
    return response.json() if response.status_code == 201 else None

def analyze_message(case_id: int, message_id: int):
    response = requests.post(
        f"{API_URL}/cases/{case_id}/messages/{message_id}/analyze",
        headers=headers
    )
    return response.json() if response.status_code == 201 else None

def delete_message(case_id: int, message_id: int):
    response = requests.delete(
        f"{API_URL}/cases/{case_id}/messages/{message_id}",
        headers=headers
    )
    return response.status_code == 204

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

# Use preselected case if coming from Cases page, or restore last selected
preselected = st.session_state.get("selected_case_id", None)
default_index = 0
if preselected:
    ids = [c['id'] for c in cases]
    if preselected in ids:
        default_index = ids.index(preselected)

selected_case_title = st.selectbox(
    "Select Case",
    options=list(case_options.keys()),
    index=default_index
)
selected_case_id = case_options[selected_case_title]
st.session_state.selected_case_id = selected_case_id  # preserve across reruns

st.divider()

# Add new message
with st.expander("➕ Add New Message", expanded=True):
    content = st.text_area(
        "Message Content",
        placeholder="Paste the message you want to analyze...",
        max_chars=2000,
        height=120,
        key="new_msg_content"
    )
    if st.button("Add & Analyze", use_container_width=True):
        if not content.strip():
            st.error("Please enter a message before analyzing.")
        else:
            with st.spinner("Adding message..."):
                message = create_message(selected_case_id, content)
            if message:
                with st.spinner("Analyzing message... this may take a moment."):
                    analysis = analyze_message(selected_case_id, message["id"])
                if analysis:
                    st.rerun()
                else:
                    st.error("Analysis failed. Please try again.")
            else:
                st.error("Failed to add message.")

st.divider()

# Message list with analysis
st.subheader("Messages in this Case")
messages = get_messages(selected_case_id)

# Search messages
msg_search = st.text_input("🔍 Search messages", placeholder="Type to filter...")
if msg_search:
    messages = [m for m in messages if msg_search.lower() in m['content'].lower() or
                (m.get('author_alias') and msg_search.lower() in m['author_alias'].lower())]

if not messages:
    st.info("No messages yet. Add your first message above.")
else:
    for msg in reversed(messages):
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
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
                    context_risk = analysis.get("context_risk_level")
                    st.markdown(risk_badge(level), unsafe_allow_html=True)
                    if context_risk:
                        colors = {"none": ("🟢", "#2d6a4f"), "low": ("🟡", "#b5850a"), "medium": ("🟠", "#b84c00"), "high": ("🔴", "#9b2226")}
                        emoji, color = colors.get(context_risk, ("⚪", "#888888"))
                        st.markdown(f'<span style="font-size:0.85rem; color:{color}; font-weight:600;">{emoji} Context: {context_risk.capitalize()}</span>', unsafe_allow_html=True)
                else:
                    confirm_key = f"confirm_delete_{msg['id']}"
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("Analyze", key=f"analyze_{msg['id']}"):
                            with st.spinner("Analyzing..."):
                                analyze_message(selected_case_id, msg['id'])
                            st.rerun()
                    with btn_col2:
                        if st.session_state.get(confirm_key):
                            if st.button("⚠️ Confirm", key=f"confirm_btn_{msg['id']}"):
                                delete_message(selected_case_id, msg['id'])
                                st.session_state.pop(confirm_key, None)
                                st.rerun()
                        else:
                            if st.button("🗑️", key=f"delete_{msg['id']}"):
                                st.session_state[confirm_key] = True
                                st.rerun()

            # Show analysis details
            if analysis_resp.status_code == 200:
                analysis = analysis_resp.json()
                if analysis.get("risk_level") != "none":
                    with st.expander("📋 View Analysis", expanded=False):
                        st.markdown("**Explanation**")
                        st.info(analysis.get("explanation", ""))
                        if analysis.get("context_note"):
                            st.caption(f"ℹ️ {analysis.get('context_note')}")

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