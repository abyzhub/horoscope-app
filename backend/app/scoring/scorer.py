"""
Event Scoring Engine — weighted scoring for major life event detection.

Scoring model:
  Natal Promise Score   (0–10)  — planetary dignity, house strength from birth chart
  Dasha Activation Score (0–10) — dasha lord's relevance to queried domain
  Transit Trigger Score  (0–10) — slow-planet transit pressure on sensitive houses

Major Event Index = 0.4 × Natal + 0.3 × Dasha + 0.3 × Transit
"""
from typing import Dict, List, Any

from app.engine.models import PlanetName, ZodiacSign
from app.engine.yoga import EXALTATION_SIGNS, DEBILITATION_SIGNS, ZODIAC_LORDS

# Domain → relevant houses (BPHS)
DOMAIN_HOUSES: Dict[str, List[int]] = {
    "career":    [1, 2, 6, 10, 11],
    "marriage":  [2, 7, 11],
    "finance":   [2, 5, 9, 11],
    "health":    [1, 6, 8, 12],
    "spiritual": [4, 9, 12],
    "general":   [1, 4, 7, 10],
}

# Slow planets whose dasha / transit matters most
POWERFUL_DASHA_LORDS = {
    PlanetName.SATURN.value:  ("career", "health", "general"),
    PlanetName.JUPITER.value: ("finance", "spiritual", "marriage", "general"),
    PlanetName.RAHU.value:    ("career", "finance", "general"),
    PlanetName.KETU.value:    ("spiritual", "health", "general"),
    PlanetName.MARS.value:    ("career", "health", "general"),
    PlanetName.VENUS.value:   ("marriage", "finance", "general"),
    PlanetName.MERCURY.value: ("career", "finance", "general"),
    PlanetName.MOON.value:    ("health", "marriage", "general"),
    PlanetName.SUN.value:     ("career", "spiritual", "general"),
}


def _natal_promise_score(natal_payload: Dict, domain: str) -> float:
    """
    Score 0–10 for how strong the natal chart is for the given domain.
    Considers exalted/own-sign planets in relevant houses.
    """
    domain_houses = set(DOMAIN_HOUSES.get(domain, DOMAIN_HOUSES["general"]))
    planets: List[Dict] = natal_payload.get("planets", [])
    score = 0.0

    for p in planets:
        p_house = p.get("house", 0)
        if p_house not in domain_houses:
            continue

        try:
            p_name_enum = PlanetName(p["name"])
        except (ValueError, KeyError):
            continue

        p_sign_str = p.get("sign", "")
        try:
            p_sign_enum = ZodiacSign(p_sign_str)
        except ValueError:
            continue

        # Exalted in domain house: strong promise
        if EXALTATION_SIGNS.get(p_name_enum) == p_sign_enum:
            score += 2.5
        # Own sign
        elif ZODIAC_LORDS.get(p_sign_enum) == p_name_enum:
            score += 1.8
        # Debilitated: promise is weak/challenged
        elif DEBILITATION_SIGNS.get(p_name_enum) == p_sign_enum:
            score -= 0.5
        else:
            score += 0.8

    return round(min(max(score, 0.0), 10.0), 2)


def _dasha_activation_score(monthly_data: Dict, domain: str) -> float:
    """
    Score 0–10 for how relevant the active Dasha lord is to the queried domain.
    """
    md_lord = monthly_data.get("mahadasha_lord", "")
    ad_lord = monthly_data.get("antardasha_lord", "")

    domains = POWERFUL_DASHA_LORDS.get(md_lord, ())
    score = 3.0 if domain in domains else 1.0

    ad_domains = POWERFUL_DASHA_LORDS.get(ad_lord, ())
    score += 2.0 if domain in ad_domains else 0.5

    # Bonus: MD lord == AD lord (double activation)
    if md_lord == ad_lord:
        score += 1.5

    return round(min(score, 10.0), 2)


def _transit_trigger_score(monthly_data: Dict, domain: str) -> float:
    """
    Score 0–10 for transit pressure on domain-relevant houses this month.
    """
    domain_houses = set(DOMAIN_HOUSES.get(domain, DOMAIN_HOUSES["general"]))
    activated = set(monthly_data.get("activated_houses", []))
    transits: List[Dict] = monthly_data.get("major_transits", [])

    overlap = len(activated & domain_houses)
    score = overlap * 1.5

    for t in transits:
        if t.get("house") in domain_houses:
            score += 1.0
            if t.get("is_retrograde"):
                score += 0.5
            score += len(t.get("conjunct_natal", [])) * 0.8

    return round(min(score, 10.0), 2)


def _dominant_theme(domain: str, monthly_data: Dict) -> str:
    themes = monthly_data.get("themes", [])
    if themes:
        return themes[0]
    return domain.title() + " Period"


def score_period(
    natal_payload: Dict,
    monthly_data: Dict,
    domain: str = "general",
) -> Dict[str, Any]:
    """
    Compute the full event score for a single month.
    Returns opportunity_score, risk_score, major_event_probability, dominant_theme.
    """
    natal_score   = _natal_promise_score(natal_payload, domain)
    dasha_score   = _dasha_activation_score(monthly_data, domain)
    transit_score = _transit_trigger_score(monthly_data, domain)

    major_event_index = (
        0.4 * natal_score
        + 0.3 * dasha_score
        + 0.3 * transit_score
    )

    # Opportunity vs Risk differentiation:
    # High intensity + strong dasha → opportunity
    # High transit in 6/8/12 without dasha support → risk
    risk_houses = set(monthly_data.get("activated_houses", [])) & {6, 8, 12}
    opp_houses  = set(monthly_data.get("activated_houses", [])) & {1, 5, 9, 10, 11}

    risk_score        = round(min(len(risk_houses) * 2.5 + (10 - dasha_score) * 0.3, 10.0), 2)
    opportunity_score = round(min(len(opp_houses) * 2.0 + dasha_score * 0.5, 10.0), 2)

    return {
        "natal_promise_score":    round(natal_score, 2),
        "dasha_activation_score": round(dasha_score, 2),
        "transit_trigger_score":  round(transit_score, 2),
        "major_event_index":      round(major_event_index, 2),
        "major_event_probability": round(major_event_index / 10.0, 3),
        "risk_score":             risk_score,
        "opportunity_score":      opportunity_score,
        "is_high_significance":   major_event_index >= 7.5,
        "dominant_theme":         _dominant_theme(domain, monthly_data),
    }
