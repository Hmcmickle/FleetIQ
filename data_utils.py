from __future__ import annotations

from io import BytesIO
from typing import Iterable

import pandas as pd

from .scoring import assess_account


REQUIRED_COLUMNS = [
    "Legal_Name",
    "Business_State",
    "Power_Units",
    "Years_In_Business",
    "Insurer",
    "Policy_Expiration_Date",
    "Safety_Rating",
    "ISS",
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


def load_cab_file(uploaded_file) -> pd.DataFrame:
    df = pd.read_excel(uploaded_file)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            "Missing expected columns: " + ", ".join(missing)
        )
    return df.copy()


def analyze_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    assessments = df.apply(assess_account, axis=1)

    df["Score"] = [a.score for a in assessments]
    df["Tier"] = [a.tier for a in assessments]
    df["Close_Probability"] = [a.close_probability for a in assessments]
    df["Carrier_Fit"] = [a.carrier_fit for a in assessments]
    df["Premium_Estimate"] = [a.premium_estimate for a in assessments]
    df["Recommended_Action"] = [a.action for a in assessments]
    df["Summary"] = [a.summary for a in assessments]
    df["Red_Flags"] = [a.red_flags for a in assessments]

    preferred_cols = [
        "Legal_Name",
        "Business_State",
        "Power_Units",
        "Years_In_Business",
        "Insurer",
        "Policy_Expiration_Date",
        "Score",
        "Tier",
        "Close_Probability",
        "Carrier_Fit",
        "Premium_Estimate",
        "Recommended_Action",
        "Summary",
        "Red_Flags",
    ]
    remainder = [c for c in df.columns if c not in preferred_cols]
    return df[preferred_cols + remainder]


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="FleetIQ_Analysis")
        workbook = writer.book
        worksheet = writer.sheets["FleetIQ_Analysis"]

        header_fmt = workbook.add_format({
            "bold": True,
            "font_color": "white",
            "bg_color": "#0F766E",
            "border": 0,
        })
        text_wrap = workbook.add_format({"text_wrap": True, "valign": "top"})
        score_fmt = workbook.add_format({"align": "center"})
        tier_a = workbook.add_format({"bg_color": "#DCFCE7"})
        tier_b = workbook.add_format({"bg_color": "#FEF3C7"})
        tier_c = workbook.add_format({"bg_color": "#FEE2E2"})

        for idx, col in enumerate(df.columns):
            worksheet.write(0, idx, col, header_fmt)
            width = min(max(len(col) + 2, 14), 38)
            worksheet.set_column(idx, idx, width)

        worksheet.set_column("L:M", 55, text_wrap)
        worksheet.set_column("N:N", 36, text_wrap)
        worksheet.set_column("G:I", 18, score_fmt)
        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)

        tier_col = df.columns.get_loc("Tier")
        for row_num, tier in enumerate(df["Tier"], start=1):
            fmt = tier_a if tier == "A" else tier_b if tier == "B" else tier_c
            worksheet.write(row_num, tier_col, tier, fmt)

    return output.getvalue()
