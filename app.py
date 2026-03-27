
import pandas as pd
import streamlit as st

st.set_page_config(page_title="FleetIQ", layout="wide")

REQUIRED_HEADERS = [
    "Legal_Name",
    "Email",
    "Company Rep1",
    "Years_In_Business",
    "Power_Units",
    "Unsafe_Driving_Score",
    "Unsafe_Driving_Alert",
    "HOS_Score",
    "HOS_Alert",
    "Driver_Fitness_Score",
    "Driver_Fitness_Alert",
    "Controlled_Substance_Score",
    "Controlled_Substance_Alert",
    "Vehicle_Maintenance_Score",
    "Vehicle_Maintenance_Alert",
    "Hazmat_Score",
    "Hazmat_Alert",
    "Crash_Score",
    "Crash_Alert",
]

def load_file(file) -> pd.DataFrame:
    df = pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def num(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value) or str(value).strip() == "":
            return default
        return float(value)
    except Exception:
        return default

def txt(value, default: str = "") -> str:
    try:
        if pd.isna(value):
            return default
        s = str(value).strip()
        return s if s else default
    except Exception:
        return default

def yn_penalty(val: str, penalty: float) -> float:
    return penalty if txt(val).upper() == "Y" else 0.0

def analyze(df: pd.DataFrame) -> pd.DataFrame:
    results = []

    for _, row in df.iterrows():
        company = txt(row.get("Legal_Name"), "Unknown Company")
        rep = txt(row.get("Company Rep1"))
        email = txt(row.get("Email"))
        years = num(row.get("Years_In_Business"), 0)
        power_units = num(row.get("Power_Units"), 0)

        unsafe = num(row.get("Unsafe_Driving_Score"), 0)
        hos = num(row.get("HOS_Score"), 0)
        driver = num(row.get("Driver_Fitness_Score"), 0)
        controlled = num(row.get("Controlled_Substance_Score"), 0)
        vehicle = num(row.get("Vehicle_Maintenance_Score"), 0)
        hazmat = num(row.get("Hazmat_Score"), 0)
        crash = num(row.get("Crash_Score"), 0)

        # Start from a neutral score so you get a spread of A/B/C.
        score = 85.0

        # Lower CAB scores are better.
        score -= unsafe * 0.35
        score -= hos * 0.30
        score -= driver * 0.20
        score -= controlled * 0.20
        score -= vehicle * 0.35
        score -= hazmat * 0.10
        score -= crash * 0.45

        # Alerts worsen the account.
        score -= yn_penalty(row.get("Unsafe_Driving_Alert"), 6)
        score -= yn_penalty(row.get("HOS_Alert"), 5)
        score -= yn_penalty(row.get("Driver_Fitness_Alert"), 4)
        score -= yn_penalty(row.get("Controlled_Substance_Alert"), 5)
        score -= yn_penalty(row.get("Vehicle_Maintenance_Alert"), 6)
        score -= yn_penalty(row.get("Hazmat_Alert"), 3)
        score -= yn_penalty(row.get("Crash_Alert"), 8)

        # Favor your target size.
        if 10 <= power_units <= 50:
            score += 6
        elif 6 <= power_units <= 75:
            score += 2
        else:
            score -= 4

        # Favor established fleets.
        if years >= 10:
            score += 4
        elif years >= 5:
            score += 2
        elif years < 2:
            score -= 5

        score = max(0, min(100, round(score, 1)))

        if score >= 72:
            tier = "A"
        elif score >= 52:
            tier = "B"
        else:
            tier = "C"

        if score >= 80:
            carrier = "Sentry / Northland"
        elif score >= 60:
            carrier = "Crum & Forster / Nirvana"
        else:
            carrier = "Canal / Cimarron"

        results.append({
            "Company": company,
            "Rep": rep,
            "Email": email,
            "Years_In_Business": years,
            "Power_Units": power_units,
            "Unsafe_Driving_Score": unsafe,
            "HOS_Score": hos,
            "Driver_Fitness_Score": driver,
            "Controlled_Substance_Score": controlled,
            "Vehicle_Maintenance_Score": vehicle,
            "Hazmat_Score": hazmat,
            "Crash_Score": crash,
            "Score": score,
            "Tier": tier,
            "Carrier": carrier,
        })

    return pd.DataFrame(results)

def split_emails(email_value: str) -> list[str]:
    if not email_value:
        return []
    clean = email_value.replace(",", ";")
    return [e.strip() for e in clean.split(";") if e.strip()]

def build_email(record: dict) -> tuple[str, str]:
    rep = txt(record.get("Rep"))
    company = txt(record.get("Company"), "your company")
    greeting_name = rep if rep else company

    unsafe = record.get("Unsafe_Driving_Score", 0)
    hos = record.get("HOS_Score", 0)
    vehicle = record.get("Vehicle_Maintenance_Score", 0)
    crash = record.get("Crash_Score", 0)
    score = record.get("Score", 0)
    tier = record.get("Tier", "C")

    issues = []
    if crash >= 60:
        issues.append(f"Crash Score {crash}")
    if unsafe >= 60:
        issues.append(f"Unsafe Driving {unsafe}")
    if hos >= 60:
        issues.append(f"HOS {hos}")
    if vehicle >= 60:
        issues.append(f"Vehicle Maintenance {vehicle}")

    if issues:
        issue_line = "The main areas that stood out were " + ", ".join(issues) + "."
    else:
        issue_line = "A few safety metrics stood out, and there may be an opportunity to improve how the account is positioned to the market."

    subject = f"Quick question on {company}'s trucking insurance"

    body = f"""Hi {greeting_name},

I was reviewing {company}'s fleet profile and wanted to reach out.

{issue_line}

Right now the account is coming in at a FleetIQ score of {score} ({tier} tier).

We work with trucking fleets to improve how they’re positioned with carriers and help uncover better options when safety metrics are affecting pricing.

Would you be open to a quick 10-minute conversation this week?

Best,
Hunter
"""
    return subject, body

st.title("FleetIQ")
st.caption("Upload CAB AI Test 2 style files. This version is mapped to your actual spreadsheet headers.")

uploaded_file = st.file_uploader("Upload CAB Excel file", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Upload your CAB file to begin.")
    st.stop()

df = load_file(uploaded_file)

missing = [h for h in REQUIRED_HEADERS if h not in df.columns]
with st.expander("Detected columns / header check", expanded=False):
    st.write(df.columns.tolist())
    if missing:
        st.warning(f"Missing headers: {missing}")
    else:
        st.success("All expected headers found.")

analyzed = analyze(df)
ranked = analyzed.sort_values("Score", ascending=False)

st.subheader("Ranked Fleets")
st.dataframe(
    ranked[["Company", "Score", "Tier"]],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Lead detail")
selected_name = st.selectbox("Select account", ranked["Company"].tolist())
selected = ranked[ranked["Company"] == selected_name].iloc[0].to_dict()

left, right = st.columns(2)

with left:
    st.write(f"**Company:** {selected['Company']}")
    st.write(f"**Rep:** {selected['Rep'] if selected['Rep'] else 'Not found'}")
    st.write(f"**Email:** {selected['Email'] if selected['Email'] else 'Not found'}")
    st.write(f"**Score:** {selected['Score']}")
    st.write(f"**Tier:** {selected['Tier']}")
    st.write(f"**Carrier:** {selected['Carrier']}")

    st.markdown("**Key scores**")
    st.write(f"- Unsafe Driving: {selected['Unsafe_Driving_Score']}")
    st.write(f"- HOS: {selected['HOS_Score']}")
    st.write(f"- Driver Fitness: {selected['Driver_Fitness_Score']}")
    st.write(f"- Controlled Substance: {selected['Controlled_Substance_Score']}")
    st.write(f"- Vehicle Maintenance: {selected['Vehicle_Maintenance_Score']}")
    st.write(f"- Hazmat: {selected['Hazmat_Score']}")
    st.write(f"- Crash: {selected['Crash_Score']}")

with right:
    st.markdown("### Customized cold email")
    subject, email_text = build_email(selected)
    st.text_input("Subject", subject)
    st.text_area("Email body", email_text, height=320)

    recipients = split_emails(selected["Email"])
    if recipients:
        st.write("**Recipients found:**", ", ".join(recipients))
    else:
        st.warning("No email found in the Email column for this account.")
