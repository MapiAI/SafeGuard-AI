# Shared UI components used across all pages.

import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

def check_auth(headers: dict) -> bool:
    try:
        response = requests.get(f"{API_URL}/me", headers=headers)
        if response.status_code in [401, 403, 404]:
            st.session_state.token = None
            st.session_state.user_email = None
            st.switch_page("app.py")
            return False
        return True
    except Exception:
        return True

def show_sidebar():
    """Render the navigation sidebar. Call at the top of every page."""
    with st.sidebar:
        st.title("🛡️ SafeGuard AI")
        st.caption(f"Logged in as {st.session_state.get('user_email', '')}")
        st.divider()
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/1_Cases.py", label="📁 Cases")
        st.page_link("pages/2_Analyze.py", label="🔍 Analyze")
        st.page_link("pages/3_Dashboard.py", label="📊 Dashboard")
        st.page_link("pages/4_RAG_Assistant.py", label="💬 Assistant")
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user_email = None
            st.switch_page("app.py")