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

    def to_num(val, default=0):
        try:
            if val is None or val == "":
                return default
            return float(val)
        except Exception:
            return default

    def get_first(row, names, default=0):
        for name in names:
            if name in row.index:
                return row.get(name, default)
        return default

    for _, row in df.iterrows():
        company = str(row.get("Legal_Name", "Unknown")).strip()

        power_units = to_num(get_first(row, ["Power Units", "Power_Units"]), 0)
        years_in_business = to_num(get_first(row, ["Years In Business", "Years_In_Business"]), 0)
        state = str(get_first(row, ["Business State", "Business_State"], "")).strip().upper()

        # EXACT / visible CAB-style column names from your screenshots
        unsafe_driving_score = to_num(row.get("Unsafe_Driving_Score", 0), 0)
        unsafe_driving_alert = str(row.get("Unsafe_Driving_Alert", "")).strip().upper()

        hos_score = to_num(row.get("HOS_Score", 0), 0)
        hos_alert = str(row.get("HOS_Alert", "")).strip().upper()

        driver_fitness_score = to_num(row.get("Driver_Fitness_Score", 0), 0)

        vehicle_maintenance_score = to_num(row.get("Vehicle_Maintenance_Score", 0), 0)
        vehicle_maintenance_alert = str(row.get("Vehicle_Maintenance_Alert", "")).strip().upper()

        hazmat_score = to_num(get_first(row, ["Hazmat_Score", "Hazmat A Score"], 0), 0)

        crash_score = to_num(row.get("Crash_Score", 0), 0)
        crash_alert = str(row.get("Crash_Alert", "")).strip().upper()

        # OOS - higher should score WORSE
        # This checks a few common header versions in case your file uses one of them
        vehicle_oos = to_num(
            get_first(
                row,
                ["Vehicle OOS %", "Vehicle_OOS_%", "Vehicle_OOS_Pct", "Vehicle OOS Pct"],
                0
            ),
            0
        )

        score = 100

        # Fleet size fit
        if 10 <= power_units <= 50:
            score += 8
        elif 6 <= power_units <= 9 or 51 <= power_units <= 75:
            score += 2
        else:
            score -= 8

        # Years in business
        if years_in_business >= 10:
            score += 8
        elif years_in_business >= 5:
            score += 4
        elif years_in_business < 2:
            score -= 10

        # Southeast bonus
        if state in southeast_states:
            score += 5

        # BASIC / CAB scores
        # Higher BASIC scores should score WORSE
        score -= unsafe_driving_score * 0.45
        score -= hos_score * 0.40
        score -= driver_fitness_score * 0.35
        score -= vehicle_maintenance_score * 0.45
        score -= hazmat_score * 0.20
        score -= crash_score * 0.65

        # Alerts
        if unsafe_driving_alert == "Y":
            score -= 8
        if hos_alert == "Y":
            score -= 8
        if vehicle_maintenance_alert == "Y":
            score -= 8
        if crash_alert == "Y":
            score -= 12

        # OOS penalty - higher OOS = WORSE score
        if vehicle_oos >= 40:
            score -= 35
        elif vehicle_oos >= 30:
            score -= 25
        elif vehicle_oos >= 20:
            score -= 15
        elif vehicle_oos >= 10:
            score -= 8
        elif vehicle_oos > 0:
            score -= 3

        # Clamp to 0-100
        score = max(0, min(100, round(score, 1)))

        # Tier
        if score >= 85:
            tier = "A"
        elif score >= 65:
            tier = "B"
        else:
            tier = "C"

        # Carrier fit
        if score >= 85:
            carrier = "Sentry / Northland"
        elif score >= 70:
            carrier = "Crum & Forster / Nirvana"
        else:
            carrier = "Canal / Cimarron"

        results.append({
            "Company": company,
            "Power Units": power_units,
            "Years In Business": years_in_business,
            "Business State": state,
            "Unsafe_Driving_Score": unsafe_driving_score,
            "Unsafe_Driving_Alert": unsafe_driving_alert,
            "HOS_Score": hos_score,
            "HOS_Alert": hos_alert,
            "Driver_Fitness_Score": driver_fitness_score,
            "Vehicle_Maintenance_Score": vehicle_maintenance_score,
            "Vehicle_Maintenance_Alert": vehicle_maintenance_alert,
            "Hazmat_Score": hazmat_score,
            "Crash_Score": crash_score,
            "Crash_Alert": crash_alert,
            "Vehicle OOS %": vehicle_oos,
            "Score": score,
            "Tier": tier,
            "Carrier": carrier
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

st.markdown("### Ranked fleets")

ranked = filtered.sort_values("Score", ascending=False)

ranked = filtered.sort_values("Score", ascending=False)

display_df = ranked[["Company", "Score", "Tier"]]

st.dataframe(
    display_df,
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
