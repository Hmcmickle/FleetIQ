from __future__ import annotations

import os
from typing import Dict

from .scoring import _safe_text

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


def fallback_email(account: Dict[str, str]) -> str:
    company = _safe_text(account.get("Legal_Name"))
    units = _safe_text(account.get("Power_Units"))
    state = _safe_text(account.get("Business_State"))
    carrier = _safe_text(account.get("Carrier_Fit"))
    premium = _safe_text(account.get("Premium_Estimate"))
    insurer = _safe_text(account.get("Insurer")) or "your current market"

    return f"""Subject: Quick idea for your {units}-truck fleet

Hi there,

I came across {company} and noticed you are running a fleet in {state}.

We help midsize fleets review coverage structure and pricing with trucking markets that fit operations like yours. Based on your profile, I would likely start with markets such as {carrier}.

At a high level, fleets like this often land around {premium}, but there can be room to improve terms depending on how {insurer} is currently set up.

If you are open to it, I can give you a quick review and tell you whether it looks worth shopping or leaving alone.

Thanks,
Hunter
"""


def ai_email(account: Dict[str, str]) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return fallback_email(account)

    client = OpenAI(api_key=api_key)
    prompt = f"""
Write a short cold email for a trucking insurance producer.

Audience:
- Midsize fleet in the Southeast
- 10 to 50 trucks
- Owner or fleet manager

Account details:
Company: {account.get("Legal_Name")}
State: {account.get("Business_State")}
Power units: {account.get("Power_Units")}
Years in business: {account.get("Years_In_Business")}
Current insurer: {account.get("Insurer")}
Recommended markets: {account.get("Carrier_Fit")}
Estimated premium: {account.get("Premium_Estimate")}
Risk summary: {account.get("Summary")}

Rules:
- Keep it under 140 words
- Sound direct and professional
- Do not be pushy
- Mention one specific detail from the account
- Include a subject line
- End with a light call to action
"""
    try:
        response = client.responses.create(
            model="gpt-5",
            input=prompt,
        )
        text = getattr(response, "output_text", "").strip()
        return text or fallback_email(account)
    except Exception:
        return fallback_email(account)
