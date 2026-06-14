# Cases page — Create, view, and manage cases.

import streamlit as st
import requests
import sys
sys.path.append("..")
from components import show_sidebar, check_auth

show_sidebar()


API_URL = "http://127.0.0.1:8000"

# ── Auth check ────────────────────────────────────────────────────────────────
if not st.session_state.get("token"):
    st.warning("Please login to access this page.")
    st.stop()

token = st.session_state.token
headers = {"Authorization": f"Bearer {token}"}
check_auth(headers)

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_cases():
    response = requests.get(f"{API_URL}/cases/", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

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
                date_parts = case['created_at'][:10].split("-")
                st.caption(f"Created: {date_parts[2]}-{date_parts[1]}-{date_parts[0]}")
            with col2:
                if st.button("🗑️", key=f"delete_{case['id']}", help="Delete case"):
                    if delete_case(case['id']):
                        st.rerun()