"""
Conversational Agent — intent detection and LLM orchestration.

The LLM receives ONLY structured astrology data (dashas, transits, scores).
It NEVER calculates planetary math itself.
"""
import re
from datetime import datetime, date, timezone
from typing import Dict, Any, Tuple, List
from enum import Enum
from pydantic import BaseModel
from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.temporal.period_analysis import analyze_period
from app.scoring.scorer import score_period, DOMAIN_HOUSES
from app.engine.karmic_cycles import calculate_all_karmic_cycles
from app.temporal.karmic_timeline import build_karmic_dashboard, get_current_cycle_status

# ─── Intent Detection ────────────────────────────────────────────────────────

class PrimaryDomain(str, Enum):
    CAREER = "career"
    MARRIAGE = "marriage"
    FINANCE = "finance"
    HEALTH = "health"
    SPIRITUAL = "spiritual"
    GENERAL = "general"

class UserIntent(BaseModel):
    primary_domain: PrimaryDomain
    timeframe_start: str # ISO Date string (YYYY-MM-DD)
    timeframe_end: str # ISO Date string (YYYY-MM-DD)
    requires_transit_math: bool

def extract_intent(question: str, current_date: date) -> UserIntent:
    """
    Use an LLM (fast, lightweight model) to parse the natural language query 
    and extract structured date boundaries and primary domain without doing math.
    """
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-your"):
        # Fallback if no API key is provided
        from dateutil.relativedelta import relativedelta
        return UserIntent(
            primary_domain=PrimaryDomain.GENERAL,
            timeframe_start=current_date.isoformat(),
            timeframe_end=(current_date + relativedelta(months=12)).isoformat(),
            requires_transit_math=True
        )

    system_prompt = (
        "You are an intent extractor for an astrology application. "
        "Do not answer the user's question. Calculate the start and end dates relative to the `current_date` provided. "
        "Map their question to the closest `primary_domain`. "
        "If they don't provide a specific timeframe, default to the next 12 months starting from `current_date`. "
        "Return dates in 'YYYY-MM-DD' ISO format. "
        "Set `requires_transit_math` to true if the question asks about a future/predictive topic or a timeframe. "
        "Set it to false ONLY if they are asking purely about static/natal chart interpretations (e.g. 'What is my Jupiter placement?')."
    )

    client = OpenAI(api_key=OPENAI_API_KEY)
    chat = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"current_date: {current_date.isoformat()}\nquestion: {question}"},
        ],
        response_format=UserIntent,
        temperature=0.0
    )
    
    return chat.choices[0].message.parsed


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
    karmic_status: Dict[str, Any] = None,
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
        f"Ascendant: {natal_summary.get('ascendant', {}).get('sign', 'Unknown')} "
        f"({natal_summary.get('ascendant', {}).get('nakshatra', 'Unknown')})",
        "",
        "Planets: " + ", ".join(
            f"{p['name']} in {p['sign']} (House {p['house']}, Nakshatra: {p.get('nakshatra', 'Unknown')})"
            for p in natal_summary.get("planets", [])
        ),
        "",
        "=== KARMIC CYCLES ==="
    ]
    
    if karmic_status:
        active = karmic_status.get("active_cycles", [])
        upcoming = karmic_status.get("upcoming_cycles", [])
        if active:
            lines.append("Active right now:")
            for a in active:
                lines.append(f"  - {a['cycle']} (Phase/Num: {a.get('phase') or a.get('number')})")
        if upcoming:
            lines.append("Upcoming soon:")
            for u in upcoming:
                lines.append(f"  - {u['cycle']} in {u.get('start') or u.get('year')}")
        if not active and not upcoming:
            lines.append("  No major active or upcoming karmic cycles tracked.")
    else:
        lines.append("  Not requested/checked purely static.")
        
    lines += [
        "",
        "=== PERIOD BEING ANALYSED ===",
        f"From {monthly_analyses[0]['period']} to {monthly_analyses[-1]['period']} ({len(monthly_analyses)} months)",
        "",
        "=== ACTIVE DASHAS BY MONTH ===",
    ]
    for m in monthly_analyses[:12]:  # Cap to 12 months for token limit
        # Get transit planets and their nakshatras
        transits = []
        for t in m.get("major_transits", []):
            nak = t.get("nakshatra")
            t_str = f"{t['planet']} in {t['sign']} ({nak})" if nak else f"{t['planet']} in {t['sign']}"
            transits.append(t_str)
            
        lines.append(
            f"  {m['period']}: {m['active_dasha']} "
            f"| Intensity {m['intensity_index']}/10 "
            f"| Houses: {m['activated_houses']} "
            f"| Transits: {', '.join(transits)}"
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

    print("\n".join(lines))
    return "\n".join(lines)


# ─── Main Agent Function ───────────────────────────────────────────────────────

def ask_agent(
    question: str,
    natal_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Full agent pipeline:
    1. LLM Intent detection (domain, timeframe)
    2. Optional Period analysis
    3. Optional Event scoring
    4. Final LLM interpretation
    """
    now = datetime.now(timezone.utc).date()
    intent = extract_intent(question, now)
    
    domain = intent.primary_domain.value
    start_date = date.fromisoformat(intent.timeframe_start)
    end_date = date.fromisoformat(intent.timeframe_end)

    monthly_analyses = []
    scored_months = []
    
    if intent.requires_transit_math:
        # Step 2 & 3: Temporal logic
        monthly_analyses = analyze_period(natal_payload, start_date, end_date)
        for m in monthly_analyses:
            score = score_period(natal_payload, m, domain)
            score["period"] = m["period"]
            scored_months.append(score)

    # Step 4: Karmic Context for LLM
    karmic_status = None
    if intent.requires_transit_math:
        all_cycles = calculate_all_karmic_cycles(natal_payload)
        dash_data = build_karmic_dashboard(all_cycles, now)
        karmic_status = get_current_cycle_status(dash_data, now)

    # Step 5: LLM call (skip if no API key configured)
    llm_response = ""
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-your"):
        client = OpenAI(api_key=OPENAI_API_KEY)
        user_prompt = _build_user_prompt(
            question, domain, natal_payload, monthly_analyses, scored_months, karmic_status
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
        "period": f"{start_date.strftime('%B %Y')} – {end_date.strftime('%B %Y')}" if intent.requires_transit_math else "Static Natal",
        "llm_interpretation": llm_response,
        "monthly_breakdown": monthly_analyses,
        "event_scores": scored_months,
        "high_significance_windows": [
            m for m in monthly_analyses if m.get("is_high_significance")
        ] if monthly_analyses else [],
    }
