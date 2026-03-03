from typing import List, Dict
from app.engine.models import PlanetPosition, ZodiacSign

ZODIAC_SIGNS = [
    ZodiacSign.ARIES, ZodiacSign.TAURUS, ZodiacSign.GEMINI, ZodiacSign.CANCER,
    ZodiacSign.LEO, ZodiacSign.VIRGO, ZodiacSign.LIBRA, ZodiacSign.SCORPIO,
    ZodiacSign.SAGITTARIUS, ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS, ZodiacSign.PISCES
]

def calculate_d9_navamsa(planet_sign: ZodiacSign, sign_degree: float) -> ZodiacSign:
    """Calculate Navamsa (D9) sign per Parashara rules."""
    sign_idx = ZODIAC_SIGNS.index(planet_sign)
    div_idx = int(sign_degree / (30.0 / 9.0))
    
    # 0, 4, 8 -> Aries (0)
    # 1, 5, 9 -> Capricorn (9)
    # 2, 6, 10 -> Libra (6)
    # 3, 7, 11 -> Cancer (3)
    start_map = {0: 0, 1: 9, 2: 6, 3: 3}
    start_sign = start_map[sign_idx % 4]
    
    d9_sign_idx = (start_sign + div_idx) % 12
    return ZODIAC_SIGNS[d9_sign_idx]

def calculate_d10_dashamsa(planet_sign: ZodiacSign, sign_degree: float) -> ZodiacSign:
    """Calculate Dashamsa (D10) sign per Parashara rules."""
    sign_idx = ZODIAC_SIGNS.index(planet_sign)
    div_idx = int(sign_degree / (30.0 / 10.0))
    
    # Odd signs start from the sign itself.
    # Even signs start from the 9th sign from itself.
    if sign_idx % 2 == 0:
        # Odd sign (Aries is 0 but it's the 1st sign)
        start_sign = sign_idx
    else:
        # Even sign
        start_sign = (sign_idx + 8) % 12
        
    d10_sign_idx = (start_sign + div_idx) % 12
    return ZODIAC_SIGNS[d10_sign_idx]

def get_divisional_charts(positions: List[PlanetPosition]) -> Dict[str, Dict[str, ZodiacSign]]:
    """
    Returns mapped signs for configured divisional charts for all input planets.
    Format: {"D9": {"Sun": "Aries", ...}, "D10": {...}}
    """
    d_charts = {
        "D9": {},
        "D10": {}
    }
    
    for p in positions:
        d_charts["D9"][p.name.value] = calculate_d9_navamsa(p.sign, p.sign_degree)
        d_charts["D10"][p.name.value] = calculate_d10_dashamsa(p.sign, p.sign_degree)
        
    return d_charts
