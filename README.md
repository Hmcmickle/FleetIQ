# FleetIQ

A polished Streamlit app for scoring CAB lead spreadsheets, matching likely carriers, and generating customized cold emails for midsize trucking fleets in the Southeast.

## Quick start

1. Create a virtual environment
2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Optional: create a `.env` file in this folder

```bash
DEMO_USERNAME=hunter
DEMO_PASSWORD=FleetIQ2026!
OPENAI_API_KEY=your_openai_api_key_here
```

4. Run the app

```bash
streamlit run app.py
```

## Default login
- Username: `hunter`
- Password: `FleetIQ2026!`

## What it expects
The uploaded CAB spreadsheet should contain these columns from your CAB export:
- Legal_Name
- Business_State
- Power_Units
- Years_In_Business
- Insurer
- Policy_Expiration_Date
- Safety_Rating
- ISS
- Unsafe_Driving_Score
- Unsafe_Driving_Alert
- HOS_Score
- HOS_Alert
- Driver_Fitness_Score
- Driver_Fitness_Alert
- Controlled_Substance_Score
- Controlled_Substance_Alert
- Vehicle_Maintenance_Score
- Vehicle_Maintenance_Alert
- Hazmat_Score
- Hazmat_Alert
- Crash_Score
- Crash_Alert

## Notes
- If `OPENAI_API_KEY` is set, FleetIQ will use AI to generate a more customized cold email.
- If not, it falls back to a strong built-in email template so you can still use it immediately.
