from __future__ import annotations

from dataclasses import dataclass
import math
import pandas as pd


SOUTHEAST_STATES = {"GA", "FL", "AL", "SC", "NC", "TN", "MS", "LA", "KY", "AR"}


@dataclass
class AccountAssessment:
    score: int
    tier: str
    close_probability: str
    carrier_fit: str
    premium_estimate: str
    action: str
    summary: str
    red_flags: str


def _safe_num(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_text(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def _alert_yes(value) -> bool:
    return _safe_text(value).lower() in {"yes", "y", "true", "1"}


def elite_score(row: pd.Series) -> int:
    score = 40  # baseline

    power_units = _safe_num(row.get("Power_Units"))
    years_in_business = _safe_num(row.get("Years_In_Business"))
    crash_score = _safe_num(row.get("Crash_Score"), 50)
    unsafe_score = _safe_num(row.get("Unsafe_Driving_Score"), 50)
    hos_score = _safe_num(row.get("HOS_Score"), 50)
    driver_fitness = _safe_num(row.get("Driver_Fitness_Score"), 50)
    controlled_sub = _safe_num(row.get("Controlled_Substance_Score"), 50)
    vehicle_maint = _safe_num(row.get("Vehicle_Maintenance_Score"), 50)
    hazmat_score = _safe_num(row.get("Hazmat_Score"), 50)
    iss = _safe_num(row.get("ISS"), 50)
    state = _safe_text(row.get("Business_State")).upper()
    safety_rating = _safe_text(row.get("Safety_Rating")).lower()
    insurer = _safe_text(row.get("Insurer"))

    # Fleet size sweet spot
    if 10 <= power_units <= 50:
        score += 15
    elif 51 <= power_units <= 100:
        score += 7
    else:
        score -= 6

    # Longevity
    if years_in_business >= 10:
        score += 10
    elif years_in_business >= 5:
        score += 6
    elif years_in_business >= 2:
        score += 2
    else:
        score -= 8

    # Core risk signals: lower CAB BASIC scores are better
    for val, good, okay, strong_penalty, mild_penalty in [
        (crash_score, 30, 60, -14, -5),
        (unsafe_score, 30, 60, -10, -4),
        (hos_score, 30, 60, -8, -3),
        (driver_fitness, 30, 60, -6, -2),
        (controlled_sub, 30, 60, -6, -2),
        (vehicle_maint, 30, 60, -8, -3),
        (hazmat_score, 30, 60, -5, -1),
        (iss, 40, 75, -8, -3),
    ]:
        if val < good:
            score += 5
        elif val < okay:
            score += 1
        elif val >= 80:
            score += strong_penalty
        else:
            score += mild_penalty

    # Alerts matter
    alert_fields = [
        "Crash_Alert",
        "Unsafe_Driving_Alert",
        "HOS_Alert",
        "Driver_Fitness_Alert",
        "Controlled_Substance_Alert",
        "Vehicle_Maintenance_Alert",
        "Hazmat_Alert",
    ]
    for field in alert_fields:
        if _alert_yes(row.get(field)):
            score -= 7

    # Safety rating / geography / stability
    if "satisfactory" in safety_rating:
        score += 5
    elif "conditional" in safety_rating:
        score -= 10
    elif "unsatisfactory" in safety_rating:
        score -= 18

    if state in SOUTHEAST_STATES:
        score += 4

    if insurer:
        score += 3

    return max(0, min(100, round(score)))


def close_probability(score: int) -> str:
    if score >= 85:
        return "High (70–85%)"
    if score >= 70:
        return "Medium (45–70%)"
    return "Low (<45%)"


def estimate_premium(row: pd.Series, score: int) -> str:
    power_units = max(1, int(_safe_num(row.get("Power_Units"), 1)))
    base_per_truck = 11250

    if score >= 85:
        base_per_truck *= 0.92
    elif score >= 70:
        base_per_truck *= 1.00
    elif score >= 55:
        base_per_truck *= 1.13
    else:
        base_per_truck *= 1.28

    total = int(base_per_truck * power_units)
    per_truck = int(base_per_truck)
    return f"${per_truck:,}/truck (~${total:,} total)"


def match_carrier(row: pd.Series, score: int) -> str:
    crash_score = _safe_num(row.get("Crash_Score"), 50)
    unsafe_score = _safe_num(row.get("Unsafe_Driving_Score"), 50)
    hos_score = _safe_num(row.get("HOS_Score"), 50)
    power_units = _safe_num(row.get("Power_Units"), 0)
    years_in_business = _safe_num(row.get("Years_In_Business"), 0)

    severe_alert = any(
        _alert_yes(row.get(field))
        for field in ["Crash_Alert", "Unsafe_Driving_Alert", "HOS_Alert", "Vehicle_Maintenance_Alert"]
    )

    if score >= 85 and crash_score < 35 and unsafe_score < 35 and years_in_business >= 5:
        return "Sentry Select / Northland"
    if score >= 72 and crash_score < 60 and hos_score < 60:
        return "Northland / Crum & Forster"
    if score >= 62 and power_units >= 15 and not severe_alert:
        return "Nirvana / Crum & Forster"
    if severe_alert or crash_score >= 60 or unsafe_score >= 60:
        return "Canal / Cimarron"
    return "Crum & Forster"


def assign_tier(score: int) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    return "C"


def recommended_action(score: int) -> str:
    if score >= 80:
        return "Quote now and prioritize outreach this week."
    if score >= 65:
        return "Work the account, but verify pain points and timing first."
    return "Use caution, qualify hard, and position with tougher markets only."


def build_summary(row: pd.Series, score: int, carrier: str) -> tuple[str, str]:
    power_units = int(_safe_num(row.get("Power_Units"), 0))
    state = _safe_text(row.get("Business_State"))
    years = int(_safe_num(row.get("Years_In_Business"), 0))
    crash = _safe_num(row.get("Crash_Score"), 50)
    unsafe = _safe_num(row.get("Unsafe_Driving_Score"), 50)
    insurer = _safe_text(row.get("Insurer")) or "current market unknown"

    positives = []
    flags = []

    if 10 <= power_units <= 50:
        positives.append("right in your 10–50 truck sweet spot")
    else:
        flags.append("outside your ideal fleet-size band")

    if years >= 5:
        positives.append(f"{years} years in business")
    else:
        flags.append("limited operating history")

    if crash < 40:
        positives.append("solid crash profile")
    elif crash >= 60:
        flags.append("elevated crash score")

    if unsafe < 40:
        positives.append("manageable unsafe driving score")
    elif unsafe >= 60:
        flags.append("elevated unsafe driving score")

    for field, label in [
        ("Crash_Alert", "crash alert"),
        ("Unsafe_Driving_Alert", "unsafe driving alert"),
        ("HOS_Alert", "HOS alert"),
        ("Vehicle_Maintenance_Alert", "vehicle maintenance alert"),
    ]:
        if _alert_yes(row.get(field)):
            flags.append(label)

    pos_text = ", ".join(positives) if positives else "mixed risk signals"
    flag_text = ", ".join(flags) if flags else "no major CAB alerts showing"

    summary = (
        f"{power_units}-unit fleet in {state}. "
        f"Best fit looks like {carrier}. "
        f"Strengths include {pos_text}. "
        f"Current insurer: {insurer}."
    )
    return summary, flag_text


def assess_account(row: pd.Series) -> AccountAssessment:
    score = elite_score(row)
    tier = assign_tier(score)
    carrier = match_carrier(row, score)
    premium = estimate_premium(row, score)
    action = recommended_action(score)
    summary, red_flags = build_summary(row, score, carrier)
    return AccountAssessment(
        score=score,
        tier=tier,
        close_probability=close_probability(score),
        carrier_fit=carrier,
        premium_estimate=premium,
        action=action,
        summary=summary,
        red_flags=red_flags,
    )
