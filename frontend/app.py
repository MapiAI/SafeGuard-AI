# SafeGuard AI — Main Streamlit app entry point.
# Handles authentication state and navigation.

import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="SafeGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide sidebar when not authenticated
if st.session_state.get("token") is None:
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# ── Auth helpers ──────────────────────────────────────────────────────────────
def login(email: str, password: str) -> bool:
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": email, "password": password}
    )
    if response.status_code == 200:
        st.session_state.token = response.json()["access_token"]
        st.session_state.user_email = email
        return True
    return False

def register(email: str, password: str) -> tuple[bool, str]:
    response = requests.post(
        f"{API_URL}/auth/register",
        json={"email": email, "password": password}
    )
    if response.status_code == 201:
        return True, "Account created successfully."
    return False, response.json().get("detail", "Registration failed.")

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if st.session_state.token is None:
        show_auth_page()
    else:
        show_main_app()

def show_auth_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🛡️ SafeGuard AI")
        st.caption("AI-Powered Detection and Analysis of Toxic Communication Patterns")
        st.divider()

        tab_login, tab_register = st.tabs(["Login", "Register"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    if login(email, password):
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

        with tab_register:
            with st.form("register_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password", help="Minimum 8 characters.")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                if submitted:
                    success, message = register(email, password)
                    if success:
                        st.success(message + " Please login.")
                    else:
                        st.error(message)

def show_main_app():
    with st.sidebar:
        st.title("🛡️ SafeGuard AI")
        st.caption(f"Logged in as {st.session_state.user_email}")
        st.divider()
        st.page_link("app.py", label="🏠 Home", icon=None)
        st.page_link("pages/1_Cases.py", label="📁 Cases")
        st.page_link("pages/2_Analyze.py", label="🔍 Analyze")
        st.page_link("pages/3_Dashboard.py", label="📊 Dashboard")
        st.page_link("pages/4_RAG_Assistant.py", label="💬 Assistant")
        st.divider()
        if st.button("Logout", use_container_width=True):
            logout()

    st.title("🛡️ SafeGuard AI")
    st.subheader("Welcome to SafeGuard AI")
    
    st.info("""
    SafeGuard AI helps you identify and understand potentially harmful communication patterns.
    
    **How to use:**
    1. Create a **Case** to group related messages
    2. Add **Messages** to your case
    3. **Analyze** messages to detect communication patterns
    4. View **Dashboard** for pattern trends over time
    5. Ask the **Assistant** educational questions
    """)

    st.warning("""
    ⚠️ **Important:** SafeGuard AI analyzes linguistic patterns only. 
    It does not diagnose individuals, assign guilt, or provide legal or psychological advice.
    For privacy, avoid using real names in messages.
    """)

main()