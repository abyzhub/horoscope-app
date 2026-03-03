from typing import List, Dict
from app.engine.models import PlanetPosition, PlanetName, ZodiacSign

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
                
    # 5. Vipareeta Raja Yoga (Simplified: 6,8,12 Lords in 6,8,12)
    # This requires full house lord logic
    # Find signs in 6, 8, 12 from ascendant
    # (asc sign + house - 1) % 12
    # But for now we omit the full logic check to save space, or just keep it simple.
    
    return yogas_detected
