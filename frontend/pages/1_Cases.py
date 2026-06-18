# Cases page — Create, view, and manage cases with message previews.

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

def create_case(title: str, description: str):
    response = requests.post(
        f"{API_URL}/cases/",
        json={"title": title, "description": description},
        headers=headers
    )
    return response.status_code == 201

def delete_case(case_id: int):
    response = requests.delete(f"{API_URL}/cases/{case_id}", headers=headers)
    return response.status_code == 204

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
st.title("📁 Cases")
st.caption("Group related messages into cases for better analysis and tracking.")
st.divider()

# Create new case
with st.expander("➕ Create New Case", expanded=False):
    with st.form("create_case_form"):
        title = st.text_input(
            "Case Title",
            placeholder="e.g. Workplace 2024, Personal relationship",
            max_chars=100
        )
        description = st.text_area(
            "Description (optional)",
            placeholder="Brief context about this case",
            max_chars=500
        )
        st.caption("⚠️ For privacy reasons, avoid using real names.")
        submitted = st.form_submit_button("Create Case", use_container_width=True)
        if submitted:
            if title:
                if create_case(title, description):
                    st.success("Case created successfully.")
                    st.rerun()
                else:
                    st.error("Failed to create case.")
            else:
                st.warning("Please enter a title.")

st.divider()

# List cases
cases = get_cases()

# Search
search = st.text_input("🔍 Search cases", placeholder="Type to filter...")
if search:
    cases = [c for c in cases if search.lower() in c['title'].lower() or
            (c['description'] and search.lower() in c['description'].lower())]

if not cases:
    st.info("No cases yet. Create your first case above.")
else:
    st.subheader(f"Your Cases ({len(cases)})")
    for case in cases:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{case['title']}**")
                if case['description']:
                    st.caption(case['description'])
                st.caption(f"Created: {format_date(case['created_at'])}")
            with col2:
                if st.button("🗑️", key=f"delete_{case['id']}", help="Delete case"):
                    if delete_case(case['id']):
                        st.rerun()

            # Case summary
            with st.expander("📊 Summary", expanded=False):
                messages = get_messages(case['id'])
                if not messages:
                    st.info("No messages yet.")
                else:
                    analyses = [get_analysis(case['id'], m['id']) for m in messages]
                    analyses = [a for a in analyses if a]
                    
                    total = len(messages)
                    analyzed = len(analyses)
                    high = sum(1 for a in analyses if a.get("risk_level") == "high")
                    medium = sum(1 for a in analyses if a.get("risk_level") == "medium")
                    low = sum(1 for a in analyses if a.get("risk_level") == "low")
                    none = sum(1 for a in analyses if a.get("risk_level") == "none")

                    st.markdown(
                        f"**{total}** messages &nbsp;|&nbsp; "
                        f"🔴 {high} &nbsp; 🟠 {medium} &nbsp; 🟡 {low} &nbsp; 🟢 {none}",
                        unsafe_allow_html=True
                    )
                    
                    if analyzed < total:
                        st.caption(f"{total - analyzed} messages not yet analyzed.")

                    col_left, col_right = st.columns(2)
                    with col_left:
                        if st.button("→ Analyze", key=f"analyze_link_{case['id']}", use_container_width=True):
                            st.session_state.selected_case_id = case['id']
                            st.switch_page("pages/2_Analyze.py")
                    with col_right:
                        if st.button("→ Dashboard", key=f"dashboard_link_{case['id']}", use_container_width=True):
                            st.session_state.selected_case_id = case['id']
                            st.switch_page("pages/3_Dashboard.py")