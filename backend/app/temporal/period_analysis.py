"""
Period analysis engine.

Given a natal chart payload + date range, produces a month-by-month
breakdown: active dasha, transit state, intensity_index.
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from dateutil.relativedelta import relativedelta

from app.temporal.transit import compute_transits
from app.engine.models import PlanetName, ZodiacSign
from app.engine.ephemeris import ZODIAC_SIGNS


def _parse_naive(iso_str: str) -> datetime:
    """Parse an ISO datetime string and strip timezone info for naive comparison."""
    dt = datetime.fromisoformat(iso_str)
    return dt.replace(tzinfo=None)


def _find_active_dasha(dashas: List[Dict], target_date: datetime) -> Dict[str, Any]:
    """Return the active Mahadasha + Antardasha for a given date."""
    result = {"mahadasha_lord": "Unknown", "antardasha_lord": "Unknown", "period_label": "Unknown"}
    for md in dashas:
        md_start = _parse_naive(md["start"])
        md_end = _parse_naive(md["end"])
        if md_start <= target_date <= md_end:
            result["mahadasha_lord"] = md["mahadasha_lord"]
            for ad in md.get("antardashas", []):
                ad_start = _parse_naive(ad["start"])
                ad_end = _parse_naive(ad["end"])
                if ad_start <= target_date <= ad_end:
                    result["antardasha_lord"] = ad["lord"]
                    break
            result["period_label"] = f"{result['mahadasha_lord']}/{result['antardasha_lord']}"
            break
    return result


def _intensity_index(activated_houses: List[int], transit_events: List[Dict]) -> float:
    """
    Compute a 0–10 intensity score for a month based on:
    - Number of sensitive houses activated by transits
    - Planets in sensitive houses
    - Retrograde slow planets
    """
    SENSITIVE = {1, 4, 7, 8, 10, 12}
    score = 0.0

    # Activated sensitive houses
    sensitive_activated = [h for h in activated_houses if h in SENSITIVE]
    score += len(sensitive_activated) * 1.2

    # Transit events detail
    for evt in transit_events:
        if evt["house"] in SENSITIVE:
            score += 0.8
        if evt["is_retrograde"]:
            score += 0.4
        score += len(evt["conjunct_natal"]) * 0.6
        score += len(evt["opposite_natal"]) * 0.5
        score += len(evt["special_aspect_houses"]) * 0.3

    return round(min(score, 10.0), 2)


def analyze_period(
    natal_payload: Dict[str, Any],
    start_date: date,
    end_date: date,
) -> List[Dict[str, Any]]:
    """
    Iterate month-by-month and return structured monthly analysis.
    """
    planets = natal_payload.get("planets", [])
    dashas = natal_payload.get("dashas", [])
    ascendant = natal_payload.get("ascendant", {})

    # Ascendant sign index
    asc_sign_str = ascendant.get("sign", "Aries")
    try:
        asc_sign_idx = [s.value for s in ZODIAC_SIGNS].index(asc_sign_str)
    except ValueError:
        asc_sign_idx = 0

    results = []
    current = datetime(start_date.year, start_date.month, 1)
    end_dt = datetime(end_date.year, end_date.month, 28)

    while current <= end_dt:
        # Active Dasha for this month
        dasha_info = _find_active_dasha(dashas, current)

        # Transits on the 1st of the month
        transit_data = compute_transits(current, planets, asc_sign_idx)
        activated_houses = transit_data["activated_houses"]
        transit_events = transit_data["transit_events"]

        intensity = _intensity_index(activated_houses, transit_events)

        # Dominant themes
        themes = _detect_themes(activated_houses, dasha_info)

        results.append({
            "period": current.strftime("%B %Y"),
            "year": current.year,
            "month": current.month,
            "active_dasha": dasha_info["period_label"],
            "mahadasha_lord": dasha_info["mahadasha_lord"],
            "antardasha_lord": dasha_info["antardasha_lord"],
            "activated_houses": activated_houses,
            "major_transits": [
                {
                    "planet": e["planet"],
                    "sign": e["sign"],
                    "house": e["house"],
                    "is_retrograde": e["is_retrograde"],
                    "conjunct_natal": e["conjunct_natal"],
                }
                for e in transit_events
            ],
            "intensity_index": intensity,
            "themes": themes,
            "is_high_significance": intensity >= 7.0,
        })

        current += relativedelta(months=1)

    return results


_HOUSE_THEMES = {
    1: "Self & Health",
    2: "Wealth & Family",
    3: "Courage & Siblings",
    4: "Home & Emotions",
    5: "Creativity & Children",
    6: "Challenges & Service",
    7: "Relationships & Partnership",
    8: "Transformation & Hidden Forces",
    9: "Fortune & Spirituality",
    10: "Career & Status",
    11: "Gains & Network",
    12: "Losses & Liberation",
}


def _detect_themes(activated_houses: List[int], dasha_info: Dict) -> List[str]:
    themes = [_HOUSE_THEMES[h] for h in activated_houses if h in _HOUSE_THEMES]
    # Add dasha-based theme if recognisable lords
    dasha_lord = dasha_info.get("mahadasha_lord", "")
    if dasha_lord in ("Saturn",):
        themes.insert(0, "Karmic Reckoning (Saturn Dasha)")
    elif dasha_lord in ("Jupiter",):
        themes.insert(0, "Expansion & Wisdom (Jupiter Dasha)")
    elif dasha_lord in ("Rahu",):
        themes.insert(0, "Ambition & Disruption (Rahu Dasha)")
    elif dasha_lord in ("Ketu",):
        themes.insert(0, "Detachment & Spirituality (Ketu Dasha)")
    return list(dict.fromkeys(themes))  # deduplicate preserving order
