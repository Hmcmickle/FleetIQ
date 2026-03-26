from __future__ import annotations

import pandas as pd
import streamlit as st
import pandas as pd

def load_cab_file(file):
    try:
        df = pd.read_excel(file)
        return df
    except Exception as e:
        return None
def analyze_dataframe(df):
    results = []

    southeast_states = {"GA", "FL", "AL", "SC", "NC", "TN", "MS", "LA"}

    for _, row in df.iterrows():
        score = 0

        company = str(row.get("Legal_Name", "Unknown")).strip()

        power_units = row.get("Power Units", 0)
        years_in_business = row.get("Years In Business", 0)
        state = str(row.get("Business State", "")).strip().upper()

        # Try to pull common CAB-style fields safely
        unsafe_pct = row.get("Unsafe Driving BASIC", None)
        hos_pct = row.get("HOS Compliance BASIC", None)
        vehicle_pct = row.get("Vehicle Maintenance BASIC", None)
        driver_pct = row.get("Driver Fitness BASIC", None)
        crash_pct = row.get("Crash Indicator BASIC", None)

        oos_pct = row.get("Vehicle OOS %", None)

        # Clean numeric values
        def to_num(val, default=0):
            try:
                if val is None or val == "":
                    return default
                return float(val)
            except Exception:
                return default

        power_units = to_num(power_units, 0)
        years_in_business = to_num(years_in_business, 0)
        unsafe_pct = to_num(unsafe_pct, None)
        hos_pct = to_num(hos_pct, None)
        vehicle_pct = to_num(vehicle_pct, None)
        driver_pct = to_num(driver_pct, None)
        crash_pct = to_num(crash_pct, None)
        oos_pct = to_num(oos_pct, None)

        # 1) Fleet size (20)
        if 10 <= power_units <= 50:
            score += 20
        elif 6 <= power_units <= 9 or 51 <= power_units <= 75:
            score += 10

        # 2) Years in business (15)
        if years_in_business >= 10:
            score += 15
        elif years_in_business >= 5:
            score += 10
        elif years_in_business >= 2:
            score += 5

        # 3) Southeast bonus (5)
        if state in southeast_states:
            score += 5

        # 4) BASIC safety scoring (25)
        basic_values = [v for v in [unsafe_pct, hos_pct, vehicle_pct, driver_pct, crash_pct] if v is not None]
        if basic_values:
            avg_basic = sum(basic_values) / len(basic_values)

            if avg_basic <= 20:
                score += 25
            elif avg_basic <= 40:
                score += 18
            elif avg_basic <= 60:
                score += 10
            elif avg_basic <= 80:
                score += 2
            else:
                score -= 10
        else:
            avg_basic = None
            score += 5  # limited credit if data is thin

        # 5) OOS / inspection quality (15)
        if oos_pct is not None:
            if oos_pct <= 10:
                score += 15
            elif oos_pct <= 20:
                score += 8
            elif oos_pct <= 30:
                score += 2
            else:
                score -= 8
        else:
            score += 5

        # 6) Carrier appetite fit (10)
        if score >= 75:
            appetite_score = 10
        elif score >= 55:
            appetite_score = 5
        else:
            appetite_score = 0
        score += appetite_score

        # Clamp score
        score = max(0, min(100, round(score)))

        # Tier
        if score >= 75:
            tier = "A"
        elif score >= 55:
            tier = "B"
        else:
            tier = "C"

        # Carrier fit
        if score >= 80:
            carrier = "Sentry Select / Northland"
        elif score >= 65:
            carrier = "Northland / Crum & Forster"
        elif score >= 50:
            carrier = "Nirvana / Crum & Forster"
        else:
            carrier = "Canal / Cimarron"

        # Basic summary
        red_flags = []
        if years_in_business < 3:
            red_flags.append("Newer operation")
        if avg_basic is not None and avg_basic > 60:
            red_flags.append("Elevated BASIC profile")
        if oos_pct is not None and oos_pct > 20:
            red_flags.append("Higher OOS %")
        if power_units < 10 or power_units > 50:
            red_flags.append("Outside target fleet band")

        if not red_flags:
            red_flags_text = "None"
        else:
            red_flags_text = ", ".join(red_flags)

        if tier == "A":
            recommended_action = "Prioritize immediately"
        elif tier == "B":
            recommended_action = "Review and position carefully"
        else:
            recommended_action = "Non-standard review only"

        results.append({
            "Company": company,
            "Power Units": power_units,
            "Business State": state,
            "Years In Business": years_in_business,
            "Score": score,
            "Tier": tier,
            "Carrier": carrier,
            "Recommended Action": recommended_action,
            "Red Flags": red_flags_text,
        })

    return pd.DataFrame(results)



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
    target_band= 0
    metric_card("10–50 unit fleets", f"{target_band:,}", "Inside your preferred size band")

st.markdown("### Filters")
f1, f2, f3 = st.columns([1, 1, 2])
with f1:
    tier_filter = st.multiselect("Tier", ["A", "B", "C"], default=["A", "B", "C"])
with f2:
    states = [ ] 
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

ranked = filtered.sort_values("Score", ascending=False)

st.dataframe(
    ranked,
    use_container_width=True,
    hide_index=True,
)


st.markdown("### Lead detail")
names = filtered["Company"].astype(str).tolist()
if not names:
    st.warning("No accounts match your current filters.")
    st.stop()

selected_name = st.selectbox("Select an account", names)
selected = filtered[filtered["Company"].astype(str) == selected_name].iloc[0].to_dict()

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
    email_text = f"Hi {selected.get('Company', 'there')},\n\nWe’d love to help with your trucking insurance needs."
    st.text_area("Email draft", value=email_text, height=320, label_visibility="collapsed")
    st.caption("You can copy, tweak, and send this outreach immediately.")
