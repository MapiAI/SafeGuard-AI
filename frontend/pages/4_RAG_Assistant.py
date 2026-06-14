# RAG Assistant page — Educational chatbot grounded in knowledge base documents.

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

usage_response = requests.get(f"{API_URL}/assistant/usage", headers=headers)
if usage_response.status_code == 200:
    remaining = usage_response.json().get("questions_remaining", 10)
    st.caption(f"💬 Questions remaining today: {remaining}")

# ── Helpers ───────────────────────────────────────────────────────────────────
def ask_assistant(question: str) -> tuple[str, int]:
    response = requests.post(
        f"{API_URL}/assistant/ask",
        json={"question": question},
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("answer", "No response."), data.get("questions_remaining", 0)
    elif response.status_code == 429:
        return response.json().get("detail", "Daily limit reached."), 0
    return "Sorry, the assistant is currently unavailable.", 0

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("💬 Educational Assistant")
st.caption("Ask questions about communication patterns, healthy relationships, and emotional wellbeing.")
st.divider()

st.info("""
**About this assistant:**
Responses are grounded exclusively in educational resources from trusted organisations 
including the National Domestic Violence Hotline, ACAS, and relationship education sources.
The assistant does not diagnose individuals, provide legal advice, or recommend specific actions.
""")

# ── Chat history ──────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ── Suggested questions ───────────────────────────────────────────────────────
if not st.session_state.chat_history:
    st.subheader("Suggested Questions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("What is gaslighting?", use_container_width=True):
            st.session_state.pending_question = "What is gaslighting?"
            st.rerun()
        if st.button("What are signs of emotional abuse?", use_container_width=True):
            st.session_state.pending_question = "What are signs of emotional abuse?"
            st.rerun()
    with col2:
        if st.button("What is coercive control?", use_container_width=True):
            st.session_state.pending_question = "What is coercive control?"
            st.rerun()
        if st.button("How can I communicate assertively?", use_container_width=True):
            st.session_state.pending_question = "How can I communicate assertively?"
            st.rerun()

# ── Handle pending question from buttons ──────────────────────────────────────
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.spinner("Searching educational resources..."):
        answer, remaining = ask_assistant(question)
    st.session_state.chat_history.append({"role": "assistant", "content": answer})
    st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────

if question := st.chat_input("Ask a question about communication patterns..."):
    if len(question) > 300:
        st.warning("Question is too long. Please keep it under 300 characters.")
    else:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Searching educational resources..."):
                answer, remaining = ask_assistant(question)
            st.write(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

# ── Clear chat ────────────────────────────────────────────────────────────────
if st.session_state.chat_history:
    if st.button("🗑️ Clear conversation", use_container_width=False):
        st.session_state.chat_history = []
        st.rerun()