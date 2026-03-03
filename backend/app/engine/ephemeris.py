import swisseph as swe
from datetime import datetime
from typing import Dict, List, Tuple
from app.engine.models import PlanetPosition, PlanetName, ZodiacSign

# Define standard BPHS mapping constants
ZODIAC_SIGNS = [
    ZodiacSign.ARIES, ZodiacSign.TAURUS, ZodiacSign.GEMINI, ZodiacSign.CANCER,
    ZodiacSign.LEO, ZodiacSign.VIRGO, ZodiacSign.LIBRA, ZodiacSign.SCORPIO,
    ZodiacSign.SAGITTARIUS, ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS, ZodiacSign.PISCES
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

SWE_PLANETS = {
    PlanetName.SUN: swe.SUN,
    PlanetName.MOON: swe.MOON,
    PlanetName.MARS: swe.MARS,
    PlanetName.MERCURY: swe.MERCURY,
    PlanetName.JUPITER: swe.JUPITER,
    PlanetName.VENUS: swe.VENUS,
    PlanetName.SATURN: swe.SATURN,
    PlanetName.RAHU: swe.TRUE_NODE, # True lunar node for BPHS
}

def get_julian_day(dt: datetime) -> float:
    """Convert UTC datetime to Julian Day."""
    # datetime should be UTC
    year, month, day = dt.year, dt.month, dt.day
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    
    # swe.julday expects year, month, day, hour in UT (Universal Time)
    return swe.julday(year, month, day, hour)

def get_sign_info(longitude: float) -> Tuple[ZodiacSign, float]:
    """Return the Zodiac Sign and the degree within that sign."""
    # Normalize longitude to 0-360
    long_norm = longitude % 360.0
    sign_index = int(long_norm / 30.0)
    sign_degree = long_norm % 30.0
    return ZODIAC_SIGNS[sign_index], sign_degree

def get_nakshatra_info(longitude: float) -> Tuple[str, int]:
    """Return the Nakshatra name and Pada (1-4)."""
    long_norm = longitude % 360.0
    # Each nakshatra is 13 degrees 20 minutes (13.3333... degrees)
    nak_length_deg = 360.0 / 27.0
    nak_index = int(long_norm / nak_length_deg)
    
    # Within the nakshatra, which pada? (4 padas per nakshatra)
    deg_in_nak = long_norm % nak_length_deg
    pada_length = nak_length_deg / 4.0
    pada = int(deg_in_nak / pada_length) + 1
    
    return NAKSHATRAS[nak_index], pada

def calculate_house(ascendant_sign_index: int, planet_sign_index: int) -> int:
    """
    Calculate the Whole Sign House (Bhav) from Ascendant.
    Ascendant sign is 1st house.
    """
    house = (planet_sign_index - ascendant_sign_index) % 12 + 1
    return house

def calculate_chart(utc_dt: datetime, lat: float, lon: float) -> Tuple[PlanetPosition, List[PlanetPosition]]:
    """
    Calculate Ascendant and Planetary positions.
    Returns (Ascendant, [Planets])
    """
    jd_ut = get_julian_day(utc_dt)
    
    # Set Sidereal mode to Lahiri
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Flag for sidereal calculations + speed
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    
    # 1. Calculate Ascendant (Lagna)
    # swe.houses_ex returns (cusps, ascmc)
    # ascmc[0] is the Ascendant
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b'W', flags)
    asc_longitude = ascmc[0]
    
    asc_sign, asc_deg = get_sign_info(asc_longitude)
    asc_nak, asc_pada = get_nakshatra_info(asc_longitude)
    asc_sign_idx = ZODIAC_SIGNS.index(asc_sign)
    
    ascendant = PlanetPosition(
        name=PlanetName.ASCENDANT,
        longitude=asc_longitude,
        sign=asc_sign,
        sign_degree=asc_deg,
        house=1,
        nakshatra=asc_nak,
        nakshatra_pada=asc_pada,
        is_retrograde=False
    )
    
    # 2. Calculate Planets
    planets = []
    for p_name, swe_id in SWE_PLANETS.items():
        # result is (lon, lat, dist, speed_lon, speed_lat, speed_dist)
        res, ret_flag = swe.calc_ut(jd_ut, swe_id, flags)
        p_long = res[0]
        p_speed = res[3] # Speed in longitude
        
        p_sign, p_deg = get_sign_info(p_long)
        p_nak, p_pada = get_nakshatra_info(p_long)
        p_sign_idx = ZODIAC_SIGNS.index(p_sign)
        p_house = calculate_house(asc_sign_idx, p_sign_idx)
        
        # True Node (Rahu) is almost always retrograde, speed < 0 means retro
        is_retro = p_speed < 0

        planets.append(PlanetPosition(
            name=p_name,
            longitude=p_long,
            sign=p_sign,
            sign_degree=p_deg,
            house=p_house,
            nakshatra=p_nak,
            nakshatra_pada=p_pada,
            is_retrograde=is_retro
        ))

    # 3. Calculate Ketu (180 degrees from Rahu)
    rahu_data = next(p for p in planets if p.name == PlanetName.RAHU)
    ketu_long = (rahu_data.longitude + 180.0) % 360.0
    k_sign, k_deg = get_sign_info(ketu_long)
    k_nak, k_pada = get_nakshatra_info(ketu_long)
    k_sign_idx = ZODIAC_SIGNS.index(k_sign)
    k_house = calculate_house(asc_sign_idx, k_sign_idx)

    planets.append(PlanetPosition(
        name=PlanetName.KETU,
        longitude=ketu_long,
        sign=k_sign,
        sign_degree=k_deg,
        house=k_house,
        nakshatra=k_nak,
        nakshatra_pada=k_pada,
        is_retrograde=rahu_data.is_retrograde # Ketu moves with Rahu
    ))

    return ascendant, planets
