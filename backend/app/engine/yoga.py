from typing import List, Dict
from app.engine.models import PlanetPosition, PlanetName, ZodiacSign
from app.engine.ephemeris import NAKSHATRAS, NAKSHATRA_LORDS

# House lords mapped by sign
ZODIAC_LORDS = {
    ZodiacSign.ARIES: PlanetName.MARS,
    ZodiacSign.TAURUS: PlanetName.VENUS,
    ZodiacSign.GEMINI: PlanetName.MERCURY,
    ZodiacSign.CANCER: PlanetName.MOON,
    ZodiacSign.LEO: PlanetName.SUN,
    ZodiacSign.VIRGO: PlanetName.MERCURY,
    ZodiacSign.LIBRA: PlanetName.VENUS,
    ZodiacSign.SCORPIO: PlanetName.MARS,
    ZodiacSign.SAGITTARIUS: PlanetName.JUPITER,
    ZodiacSign.CAPRICORN: PlanetName.SATURN,
    ZodiacSign.AQUARIUS: PlanetName.SATURN,
    ZodiacSign.PISCES: PlanetName.JUPITER
}

EXALTATION_SIGNS = {
    PlanetName.SUN: ZodiacSign.ARIES,
    PlanetName.MOON: ZodiacSign.TAURUS,
    PlanetName.MARS: ZodiacSign.CAPRICORN,
    PlanetName.MERCURY: ZodiacSign.VIRGO,
    PlanetName.JUPITER: ZodiacSign.CANCER,
    PlanetName.VENUS: ZodiacSign.PISCES,
    PlanetName.SATURN: ZodiacSign.LIBRA,
}

DEBILITATION_SIGNS = {
    PlanetName.SUN: ZodiacSign.LIBRA,
    PlanetName.MOON: ZodiacSign.SCORPIO,
    PlanetName.MARS: ZodiacSign.CANCER,
    PlanetName.MERCURY: ZodiacSign.PISCES,
    PlanetName.JUPITER: ZodiacSign.CAPRICORN,
    PlanetName.VENUS: ZodiacSign.VIRGO,
    PlanetName.SATURN: ZodiacSign.ARIES,
}

def is_kendra(house: int) -> bool:
    return house in [1, 4, 7, 10]

def is_trikona(house: int) -> bool:
    return house in [1, 5, 9]

def detect_yogas(ascendant: PlanetPosition, planets: List[PlanetPosition]) -> List[Dict]:
    """
    Detect basic BPHS Yogas from the planetary positions.
    """
    yogas_detected = []
    
    # Helper lookups
    p_by_name = {p.name: p for p in planets}
    p_by_house = {i: [] for i in range(1, 13)}
    for p in planets:
        p_by_house[p.house].append(p)
        
    moon = p_by_name.get(PlanetName.MOON)
    jup = p_by_name.get(PlanetName.JUPITER)
    mars = p_by_name.get(PlanetName.MARS)
    merc = p_by_name.get(PlanetName.MERCURY)
    sun = p_by_name.get(PlanetName.SUN)
    sat = p_by_name.get(PlanetName.SATURN)
    ven = p_by_name.get(PlanetName.VENUS)
    
    # 1. Gajakesari Yoga
    if moon and jup:
        # Distance between Moon and Jupiter must be Kendra (1, 4, 7, 10)
        dist = (jup.house - moon.house) % 12 + 1
        if is_kendra(dist):
            yogas_detected.append({
                "name": "Gajakesari Yoga",
                "description": "Jupiter in Kendra from Moon. Endows wealth, intelligence, and noble virtues."
            })
            
    # 2. Budh-Aditya Yoga
    if sun and merc:
        if sun.house == merc.house:
            yogas_detected.append({
                "name": "Budh-Aditya Yoga",
                "description": "Sun and Mercury conjunct. Bestows high intelligence, skill in speech, and reputation."
            })
            
    # 3. Chandra-Mangal Yoga
    if moon and mars:
        if moon.house == mars.house:
            yogas_detected.append({
                "name": "Chandra-Mangal Yoga",
                "description": "Moon and Mars conjunct. Indicates financial success but can cause restlessness."
            })
            # To-do: Mutual aspect (7th house)
            
    # 4. Panch Mahapurusha Yogas
    # Non-luminary in own or exaltation sign AND in Kendra from Asc
    pmp_planets = [mars, merc, jup, ven, sat]
    pmp_names = {
        PlanetName.MARS: "Ruchaka",
        PlanetName.MERCURY: "Bhadra",
        PlanetName.JUPITER: "Hamsa",
        PlanetName.VENUS: "Malavya",
        PlanetName.SATURN: "Sasha"
    }
    
    for p in pmp_planets:
        if p and is_kendra(p.house):
            is_own_sign = ZODIAC_LORDS[p.sign] == p.name
            is_exalted = EXALTATION_SIGNS.get(p.name) == p.sign
            if is_own_sign or is_exalted:
                y_name = f"{pmp_names[p.name]} Mahapurusha Yoga"
                yogas_detected.append({
                    "name": y_name,
                    "description": f"{p.name.value} in great dignity in a Kendra. Creates a powerful prominent personality."
                })
                
    # 6. Nakshatra Parivartana (Exchange of Nakshatra Lords)
    for p1 in planets:
        # Skip Ascendant or nodes if we strictly want 7 classic planets, but nodes are valid
        if p1.name == PlanetName.ASCENDANT:
            continue
            
        try:
            p1_nak_idx = NAKSHATRAS.index(p1.nakshatra)
            p1_nak_lord = NAKSHATRA_LORDS[p1_nak_idx]
        except ValueError:
            continue
            
        for p2 in planets:
            if p1 == p2 or p2.name == PlanetName.ASCENDANT:
                continue
                
            try:
                p2_nak_idx = NAKSHATRAS.index(p2.nakshatra)
                p2_nak_lord = NAKSHATRA_LORDS[p2_nak_idx]
            except ValueError:
                continue
                
            # Mutual exchange of Nakshatras 
            # p1 sits in p2's nakshatra AND p2 sits in p1's nakshatra
            if p1_nak_lord == p2.name and p2_nak_lord == p1.name:
                # Add only once (p1 name < p2 name to avoid duplicates)
                if p1.name.value < p2.name.value:
                    yogas_detected.append({
                        "name": f"Nakshatra Parivartana: {p1.name.value} & {p2.name.value}",
                        "description": f"Powerful inner resonance: {p1.name.value} and {p2.name.value} have exchanged Nakshatras, deeply linking their significations."
                    })
                    
    # 7. Nakshatra Raj Yoga (Kendra Lord in Trikona Lord's Nakshatra)
    for p in planets:
        if p.name == PlanetName.ASCENDANT:
            continue
        try:
            nak_idx = NAKSHATRAS.index(p.nakshatra)
            nak_lord_name = NAKSHATRA_LORDS[nak_idx]
        except ValueError:
            continue
            
        nak_lord_planet = p_by_name.get(nak_lord_name)
        if not nak_lord_planet:
            continue
            
        if is_kendra(p.house) and is_trikona(nak_lord_planet.house):
            yogas_detected.append({
                "name": f"Nakshatra Raj Yoga",
                "description": f"{p.name.value} (in a Kendra) is seated in the Nakshatra of {nak_lord_name.value} (in a Trikona). Elevates status and destiny."
            })
    
    return yogas_detected
