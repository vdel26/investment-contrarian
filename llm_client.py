import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict

# Load .env if present
load_dotenv()

# Load credentials and model name from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")

# Configure OpenAI client (v1 interface)
_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

_SYSTEM_PROMPT = (
    "You are a seasoned macro and equity strategist writing short-form market commentary. "
    "Tone: objective, concise, actionable, no hype. "
    "Audience: professional investors with contrarian tilt. "
    "Limit output to about 40 words (≈25% shorter). Plain text, no markdown, no emojis."
)


def _call_openai(messages) -> str:
    """Internal helper that calls OpenAI ChatCompletion and returns the assistant message text.
    Falls back to placeholder string on any error or missing API key."""
    if _client is None:
        return "LLM key not configured."
    try:
        response = _client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=120,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        # Log locally and return placeholder to keep pipeline alive
        print(f"⚠️ LLM call failed: {exc}")
        return "Commentary unavailable."  # front-end friendly fallback


def generate_fng_commentary(fng_summary: Dict) -> str:
    """Generate commentary for the CNN Fear & Greed index.

    Parameters
    ----------
    fng_summary : dict
        Should contain at least 'score' and 'rating'.
    """
    user_prompt = (
        f"CNN Fear & Greed index reading: {fng_summary.get('score')} "
        f"({fng_summary.get('rating').upper()}). "
        "Compose a 2–3-sentence interpretation of what this level historically implies for next-month S&P 500 risk-reward. "
        "Highlight contrarian angle if sentiment is extreme."
    )
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    return _call_openai(messages)


def generate_aaii_commentary(aaii_data: Dict) -> str:
    """Generate concise interpretation for AAII Sentiment Survey.
    Expects keys: bullish, bearish, spread (bullish-bearish)."""
    try:
        bull = aaii_data.get("bullish")
        bear = aaii_data.get("bearish")
        spread = round(float(bull) - float(bear), 1) if bull is not None and bear is not None else None
    except Exception:
        bull = bear = spread = None

    user_prompt = (
        f"AAII weekly survey: Bull {bull}%, Bear {bear}% (Spread {spread} pp). "
        "Write a 2–3-sentence contrarian interpretation of this sentiment mix and what it historically precedes for equities in the next 8–12 weeks." 
    )
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    return _call_openai(messages)


def generate_overall_analysis(fng: Dict, aaii: Dict, ssi: Dict = None) -> Dict:
    """Return {'recommendation': <word>, 'commentary': <text>} using sentiment sources."""
    score = fng.get("score")
    rating = fng.get("rating")
    bull = aaii.get("bullish")
    bear = aaii.get("bearish")
    spread = round(float(bull) - float(bear), 1) if bull is not None and bear is not None else None

    # Build the prompt with F&G and AAII data
    prompt_parts = [
        "Act as a veteran contrarian investor reviewing sentiment data. ",
        f"CNN Fear & Greed: {score} ({rating}). AAII Bull {bull}%, Bear {bear}% (Spread {spread} pp). "
    ]
    
    # Add SSI data if available
    if ssi and isinstance(ssi, list) and len(ssi) > 0:
        # Get the latest SSI value
        latest_ssi = ssi[-1]  # Assuming sorted chronologically
        ssi_level = latest_ssi.get("level")
        ssi_date = latest_ssi.get("date")
        if ssi_level and ssi_date:
            prompt_parts.append(f"BofA SSI: {ssi_level}% ({ssi_date}). ")
    
    prompt_parts.append(
        "Issue a ONE-WORD recommendation from: STRONG SELL, SELL, HOLD, BUY, STRONG BUY, followed by a 35–40-word rationale. "
        "Format exactly as: RECOMMENDATION: <word>\nCOMMENTARY: <text>."
    )
    
    user_prompt = "".join(prompt_parts)

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    raw = _call_openai(messages)
    rec = "HOLD"; commentary = raw
    try:
        for line in raw.split("\n"):
            if line.upper().startswith("RECOMMENDATION"):
                rec = line.split(":",1)[1].strip().upper()
            elif line.upper().startswith("COMMENTARY"):
                commentary = line.split(":",1)[1].strip()
    except Exception:
        pass
    return {"recommendation": rec, "commentary": commentary} 