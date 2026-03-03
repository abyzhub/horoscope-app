"""
Conversational Agent — intent detection and LLM orchestration.

The LLM receives ONLY structured astrology data (dashas, transits, scores).
It NEVER calculates planetary math itself.
"""
import re
from datetime import datetime, date, timezone
from typing import Dict, Any, Tuple, List

from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.temporal.period_analysis import analyze_period
from app.scoring.scorer import score_period, DOMAIN_HOUSES

# ─── Intent Detection ────────────────────────────────────────────────────────

DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "career":    ["career", "job", "work", "profession", "business", "promotion", "success"],
    "marriage":  ["marriage", "relationship", "partner", "spouse", "love", "wedding"],
    "finance":   ["money", "finance", "wealth", "income", "investment", "debt"],
    "health":    ["health", "sickness", "illness", "disease", "body", "hospital"],
    "spiritual": ["spiritual", "moksha", "meditation", "karma", "dharma"],
}


def detect_intent(question: str) -> str:
    q_lower = question.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            return domain
    return "general"


def extract_timeframe(question: str) -> Tuple[date, date]:
    """
    Extract a date range from natural language.
    Defaults to the current calendar year if nothing found.
    """
    now = datetime.now(timezone.utc)
    q_lower = question.lower()

    # "next year" / "next 12 months"
    if "next year" in q_lower:
        start = date(now.year + 1, 1, 1)
        return start, date(now.year + 1, 12, 31)

    # "this year" / "current year"
    if "this year" in q_lower or "current year" in q_lower:
        return date(now.year, 1, 1), date(now.year, 12, 31)

    # "next 6 months"
    m = re.search(r"next (\d+) months?", q_lower)
    if m:
        months = int(m.group(1))
        from dateutil.relativedelta import relativedelta
        end = now.date() + relativedelta(months=months)
        return now.date(), end

    # "in 2027" or "year 2027"
    m = re.search(r"\b(20\d{2})\b", question)
    if m:
        yr = int(m.group(1))
        return date(yr, 1, 1), date(yr, 12, 31)

    # Default: next 12 months from today
    from dateutil.relativedelta import relativedelta
    return now.date(), (now.date() + relativedelta(months=12))


# ─── LLM Prompt Builder ───────────────────────────────────────────────────────

SAFETY_RULES = """
IMPORTANT RULES:
- You are an Vedic astrology assistant explaining patterns in structured chart data.
- Never claim inevitability. Use language like "tendency", "theme", "window of heightened activity".
- Never make definitive health or legal predictions.
- Always frame insights as probabilities and themes.
- Do not perform any planetary math — only interpret the structured data provided.
"""


def _build_system_prompt() -> str:
    return (
        "You are a wise, knowledgeable Vedic astrology guide who explains "
        "astrological patterns clearly and compassionately. "
        "You receive structured JSON data computed by a precise Swiss Ephemeris engine "
        "and explain what the patterns suggest — never what they definitively predict.\n\n"
        + SAFETY_RULES
    )


def _build_user_prompt(
    question: str,
    domain: str,
    natal_summary: Dict,
    monthly_analyses: List[Dict],
    scores: List[Dict],
) -> str:
    # Find highlighted months
    highlights = [
        m for m in monthly_analyses if m.get("is_high_significance")
    ]

    lines = [
        f"User Question: {question}",
        f"Detected Domain: {domain}",
        "",
        "=== NATAL CHART SUMMARY ===",
        f"Ascendant: {natal_summary.get('ascendant', {}).get('sign', 'Unknown')}",
        "Planets: " + ", ".join(
            f"{p['name']} in {p['sign']} (House {p['house']})"
            for p in natal_summary.get("planets", [])
        ),
        "",
        "=== PERIOD BEING ANALYSED ===",
        f"From {monthly_analyses[0]['period']} to {monthly_analyses[-1]['period']} ({len(monthly_analyses)} months)",
        "",
        "=== ACTIVE DASHAS BY MONTH ===",
    ]
    for m in monthly_analyses[:12]:  # Cap to 12 months for token limit
        lines.append(
            f"  {m['period']}: {m['active_dasha']} "
            f"| Intensity {m['intensity_index']}/10 "
            f"| Houses: {m['activated_houses']}"
        )

    lines.append("")
    lines.append("=== HIGH SIGNIFICANCE MONTHS ===")
    if highlights:
        for h in highlights:
            lines.append(
                f"  ★ {h['period']} — {h['themes']} "
                f"(Intensity {h['intensity_index']})"
            )
    else:
        lines.append("  None found above threshold in this window.")

    if scores:
        peak = max(scores, key=lambda s: s.get("major_event_index", 0))
        lines += [
            "",
            "=== PEAK EVENT SCORE ===",
            f"  Month: {peak.get('period', 'N/A')}",
            f"  Major Event Index: {peak.get('major_event_index', 'N/A')}/10",
            f"  Opportunity Score: {peak.get('opportunity_score', 'N/A')}/10",
            f"  Risk Score: {peak.get('risk_score', 'N/A')}/10",
            f"  Dominant Theme: {peak.get('dominant_theme', 'N/A')}",
        ]

    lines += [
        "",
        "Please provide a clear, insightful, compassionate interpretation focused on the "
        f"'{domain}' domain. Use paragraph form. Mention specific months where relevant. "
        "End with 1-2 actionable suggestions for this period.",
    ]

    return "\n".join(lines)


# ─── Main Agent Function ───────────────────────────────────────────────────────

def ask_agent(
    question: str,
    natal_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Full agent pipeline:
    1. Intent detection
    2. Timeframe extraction
    3. Period analysis
    4. Event scoring
    5. LLM interpretation
    """
    domain = detect_intent(question)
    start_date, end_date = extract_timeframe(question)

    # Step 3: Temporal period analysis
    monthly_analyses = analyze_period(natal_payload, start_date, end_date)

    # Step 4: Score each month
    scored_months = []
    for m in monthly_analyses:
        score = score_period(natal_payload, m, domain)
        score["period"] = m["period"]
        scored_months.append(score)

    # Step 5: LLM call (skip if no API key configured)
    llm_response = ""
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-your"):
        client = OpenAI(api_key=OPENAI_API_KEY)
        user_prompt = _build_user_prompt(
            question, domain, natal_payload, monthly_analyses, scored_months
        )
        chat = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _build_system_prompt()},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=900,
        )
        llm_response = chat.choices[0].message.content or ""
    else:
        llm_response = (
            "⚠️ LLM response unavailable — please set OPENAI_API_KEY in backend/.env. "
            "The structured astrological data below is fully computed and accurate."
        )

    return {
        "question": question,
        "domain": domain,
        "period": f"{start_date.strftime('%B %Y')} – {end_date.strftime('%B %Y')}",
        "llm_interpretation": llm_response,
        "monthly_breakdown": monthly_analyses,
        "event_scores": scored_months,
        "high_significance_windows": [
            m for m in monthly_analyses if m.get("is_high_significance")
        ],
    }
