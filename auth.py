from __future__ import annotations

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_demo_credentials() -> tuple[str, str]:
    username = os.getenv("DEMO_USERNAME", "hunter")
    password = os.getenv("DEMO_PASSWORD", "FleetIQ2026!")
    return username, password


def ensure_login() -> None:
    if st.session_state.get("authenticated"):
        return

    st.markdown(
        """
        <div style="padding: 1.25rem 1.5rem; background: white; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(15,23,42,0.06);">
          <h2 style="margin:0; color:#0F172A;">Welcome to FleetIQ</h2>
          <p style="margin:0.5rem 0 0; color:#475569;">Login to access your underwriting dashboard.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    valid_username, valid_password = get_demo_credentials()

    if submitted:
        if username == valid_username and password == valid_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid username or password.")
