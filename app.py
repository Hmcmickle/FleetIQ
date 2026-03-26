from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.auth import ensure_login, get_demo_credentials
from modules.data_utils import analyze_dataframe, dataframe_to_excel_bytes, load_cab_file
from modules.email_generator import ai_email


st.set_page_config(
    page_title="FleetIQ",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)


def metric_card(label: str, value: str, subtext: str = "") -> None:
    st.markdown(
        f"""
        <div style="background:white; border:1px solid #E2E8F0; border-radius:18px; padding:1rem 1.1rem; box-shadow:0 8px 22px rgba(15,23,42,0.04);">
          <div style="font-size:0.86rem; color:#64748B;">{label}</div>
          <div style="font-size:1.65rem; font-weight:700; color:#0F172A; margin-top:0.15rem;">{value}</div>
          <div style="font-size:0.82rem; color:#475569; margin-top:0.2rem;">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


ensure_login()
demo_user, demo_password = get_demo_credentials()

with st.sidebar:
    st.markdown("## FleetIQ")
    st.caption("AI underwriting + prospecting for midsize trucking fleets")
    if st.button("Log out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

st.title("FleetIQ")
st.caption("Light-mode underwriting dashboard for 10–50 truck fleets in the Southeast")

tab1, tab2 = st.tabs(["Dashboard", "Quick Start"])

with tab2:
    st.markdown(
        f"""
        ### Login details
        **Username:** `{demo_user}`  
        **Password:** `{demo_password}`

        ### How to use
        1. Upload your CAB export Excel file.
        2. Review scored fleets and carrier fit.
        3. Click a row in the selector to generate a customized cold email.
        4. Export the analyzed workbook.

        ### AI email note
        Add an `OPENAI_API_KEY` in a `.env` file to enable AI-generated cold emails.  
        Without that key, FleetIQ still works and uses a strong fallback email template.
        """
    )

uploaded_file = st.file_uploader("Upload CAB Excel file", type=["xlsx"])

if not uploaded_file:
    st.info("Upload your CAB file to begin.")
    st.stop()

try:
    raw_df = load_cab_file(uploaded_file)
    analyzed_df = analyze_dataframe(raw_df)
except Exception as exc:
    st.error(str(exc))
    st.stop()

left, middle, right, far_right = st.columns(4)
with left:
    metric_card("Accounts loaded", f"{len(analyzed_df):,}", "Rows processed from your CAB file")
with middle:
    a_count = int((analyzed_df["Tier"] == "A").sum())
    metric_card("A-tier fleets", f"{a_count:,}", "Highest priority targets")
with right:
    avg_score = round(float(analyzed_df["Score"].mean()), 1)
    metric_card("Average score", str(avg_score), "Across all uploaded fleets")
with far_right:
    target_band = int(((analyzed_df["Power_Units"].fillna(0).astype(float).between(10, 50))).sum())
    metric_card("10–50 unit fleets", f"{target_band:,}", "Inside your preferred size band")

st.markdown("### Filters")
f1, f2, f3 = st.columns([1, 1, 2])
with f1:
    tier_filter = st.multiselect("Tier", ["A", "B", "C"], default=["A", "B", "C"])
with f2:
    states = sorted([s for s in analyzed_df["Business_State"].dropna().astype(str).unique().tolist() if s])
    state_filter = st.multiselect("State", states, default=states[:10] if len(states) > 10 else states)
with f3:
    search_term = st.text_input("Search company", placeholder="Start typing a legal name")

filtered = analyzed_df[analyzed_df["Tier"].isin(tier_filter)].copy()
if state_filter:
    filtered = filtered[filtered["Business_State"].astype(str).isin(state_filter)]
if search_term:
    filtered = filtered[filtered["Legal_Name"].astype(str).str.contains(search_term, case=False, na=False)]

display_cols = [
    "Legal_Name",
    "Business_State",
    "Power_Units",
    "Score",
    "Tier",
    "Carrier_Fit",
    "Close_Probability",
    "Premium_Estimate",
]
st.markdown("### Ranked fleets")
st.dataframe(
    filtered[display_cols].sort_values(["Score", "Power_Units"], ascending=[False, False]),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download analyzed workbook",
    data=dataframe_to_excel_bytes(filtered.sort_values("Score", ascending=False)),
    file_name="FleetIQ_Analysis.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

st.markdown("### Lead detail")
names = filtered["Legal_Name"].astype(str).tolist()
if not names:
    st.warning("No accounts match your current filters.")
    st.stop()

selected_name = st.selectbox("Select an account", names)
selected = filtered[filtered["Legal_Name"].astype(str) == selected_name].iloc[0].to_dict()

detail_left, detail_right = st.columns([1.1, 0.9])

with detail_left:
    st.markdown(
        f"""
        <div style="background:white; border:1px solid #E2E8F0; border-radius:20px; padding:1.2rem 1.3rem; box-shadow:0 10px 24px rgba(15,23,42,0.05);">
          <h3 style="margin:0; color:#0F172A;">{selected.get("Legal_Name","")}</h3>
          <p style="margin:0.45rem 0 0; color:#475569;">{selected.get("Business_State","")} • {int(float(selected.get("Power_Units",0) or 0))} power units</p>
          <hr style="border:none; border-top:1px solid #E2E8F0; margin:1rem 0;">
          <p><strong>Score:</strong> {selected.get("Score")}</p>
          <p><strong>Tier:</strong> {selected.get("Tier")}</p>
          <p><strong>Carrier fit:</strong> {selected.get("Carrier_Fit")}</p>
          <p><strong>Close probability:</strong> {selected.get("Close_Probability")}</p>
          <p><strong>Premium estimate:</strong> {selected.get("Premium_Estimate")}</p>
          <p><strong>Recommended action:</strong> {selected.get("Recommended_Action")}</p>
          <p><strong>Summary:</strong> {selected.get("Summary")}</p>
          <p><strong>Red flags:</strong> {selected.get("Red_Flags")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with detail_right:
    st.markdown("#### Customized cold email")
    email_text = ai_email(selected)
    st.text_area("Email draft", value=email_text, height=320, label_visibility="collapsed")
    st.caption("You can copy, tweak, and send this outreach immediately.")
