"""
Transit calculator — computes current positions of slow planets
for a given UTC datetime and compares them against natal planets/houses.

Does NOT re-use the natal chart calculation path.
Only reads from swisseph directly.
"""
import swisseph as swe
from datetime import datetime
from typing import List, Dict, Any

from app.engine.ephemeris import (
    get_julian_day,
    get_sign_info,
    ZODIAC_SIGNS,
    SWE_PLANETS,
)
from app.engine.models import PlanetName, ZodiacSign

# Slow-moving planets we track for transit analysis (per BPHS)
TRANSIT_PLANETS = [
    PlanetName.SATURN,
    PlanetName.JUPITER,
    PlanetName.MARS,
    PlanetName.RAHU,
]

# Houses considered "sensitive" for event triggering (BPHS)
SENSITIVE_HOUSES = {1, 4, 7, 8, 10, 12}


def _get_transit_positions(utc_dt: datetime) -> Dict[PlanetName, Dict[str, Any]]:
    """Return sidereal sign + house-sign index for each transit planet."""
    jd = get_julian_day(utc_dt)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

    positions: Dict[PlanetName, Dict[str, Any]] = {}
    for p_name in TRANSIT_PLANETS:
        swe_id = SWE_PLANETS[p_name]
        res, _ = swe.calc_ut(jd, swe_id, flags)
        sign, deg = get_sign_info(res[0])
        positions[p_name] = {
            "sign": sign.value,
            "sign_index": ZODIAC_SIGNS.index(sign),
            "degree": round(deg, 2),
            "is_retrograde": res[3] < 0,
        }

    # Ketu = Rahu + 180°
    rahu_idx = positions[PlanetName.RAHU]["sign_index"]
    ketu_sign_idx = (rahu_idx + 6) % 12
    positions[PlanetName.KETU] = {
        "sign": ZODIAC_SIGNS[ketu_sign_idx].value,
        "sign_index": ketu_sign_idx,
        "degree": positions[PlanetName.RAHU]["degree"],
        "is_retrograde": positions[PlanetName.RAHU]["is_retrograde"],
    }

    return positions


def compute_transits(
    utc_dt: datetime,
    natal_planets: List[Dict],
    natal_asc_sign_index: int,
) -> Dict[str, Any]:
    """
    Compare transit positions to natal chart.
    Returns detailed transit events and activated houses.
    """
    transit_pos = _get_transit_positions(utc_dt)

    activated_houses: set = set()
    transit_events: List[Dict] = []

    # Build quick lookup: natal sign_index per planet
    natal_sign_by_name: Dict[str, int] = {}
    for np in natal_planets:
        sign_str = np.get("sign", "")
        try:
            idx = [s.value for s in ZODIAC_SIGNS].index(sign_str)
        except ValueError:
            idx = 0
        natal_sign_by_name[np.get("name", "")] = idx

    for t_planet, t_data in transit_pos.items():
        t_sign_idx = t_data["sign_index"]
        # House = (transit_sign - asc_sign) % 12 + 1
        house = (t_sign_idx - natal_asc_sign_index) % 12 + 1

        if house in SENSITIVE_HOUSES:
            activated_houses.add(house)

        # Check conjunction with natal planets (same sign = conjunct in whole-sign)
        conjunct_natal: List[str] = []
        for n_name, n_sign_idx in natal_sign_by_name.items():
            if n_sign_idx == t_sign_idx:
                conjunct_natal.append(n_name)

        # 7th-aspect check for Saturn and Jupiter (full aspect in BPHS)
        opposites = []
        if t_planet in (PlanetName.SATURN, PlanetName.JUPITER, PlanetName.RAHU, PlanetName.KETU):
            opp_sign_idx = (t_sign_idx + 6) % 12
            opp_house = (opp_sign_idx - natal_asc_sign_index) % 12 + 1
            if opp_house in SENSITIVE_HOUSES:
                activated_houses.add(opp_house)
            for n_name, n_sign_idx in natal_sign_by_name.items():
                if n_sign_idx == opp_sign_idx:
                    opposites.append(n_name)

        # Special aspects for Saturn (3rd, 10th) and Jupiter (5th, 9th)
        special_aspect_houses = []
        if t_planet == PlanetName.SATURN:
            for offset in (2, 9):  # 3rd and 10th from transit sign (0-indexed)
                asp_sign = (t_sign_idx + offset) % 12
                asp_house = (asp_sign - natal_asc_sign_index) % 12 + 1
                special_aspect_houses.append(asp_house)
                if asp_house in SENSITIVE_HOUSES:
                    activated_houses.add(asp_house)
        elif t_planet == PlanetName.JUPITER:
            for offset in (4, 8):  # 5th and 9th from transit sign (0-indexed)
                asp_sign = (t_sign_idx + offset) % 12
                asp_house = (asp_sign - natal_asc_sign_index) % 12 + 1
                special_aspect_houses.append(asp_house)
                if asp_house in SENSITIVE_HOUSES:
                    activated_houses.add(asp_house)

        transit_events.append({
            "planet": t_planet.value,
            "sign": t_data["sign"],
            "degree": t_data["degree"],
            "house": house,
            "is_retrograde": t_data["is_retrograde"],
            "conjunct_natal": conjunct_natal,
            "opposite_natal": opposites,
            "special_aspect_houses": special_aspect_houses,
        })

    return {
        "activated_houses": sorted(list(activated_houses)),
        "transit_events": transit_events,
    }
