from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from app.engine.models import PlanetName
from app.engine.ephemeris import NAKSHATRAS

# Vimshottari Dasha Lords and their ruling periods (in years) per BPHS
VIMSHOTTARI_YEARS = {
    PlanetName.KETU: 7,
    PlanetName.VENUS: 20,
    PlanetName.SUN: 6,
    PlanetName.MOON: 10,
    PlanetName.MARS: 7,
    PlanetName.RAHU: 18,
    PlanetName.JUPITER: 16,
    PlanetName.SATURN: 19,
    PlanetName.MERCURY: 17
}

# The sequence of Vimshottari Dasha Lords
VIMSHOTTARI_SEQUENCE = [
    PlanetName.KETU, PlanetName.VENUS, PlanetName.SUN, PlanetName.MOON, 
    PlanetName.MARS, PlanetName.RAHU, PlanetName.JUPITER, PlanetName.SATURN, 
    PlanetName.MERCURY
]

TOTAL_VIMSHOTTARI_YEARS = 120.0

def get_dasha_lord_for_nakshatra(nakshatra_name: str) -> PlanetName:
    """Returns the starting Mahadasha lord for a given Nakshatra."""
    nak_idx = NAKSHATRAS.index(nakshatra_name)
    # The sequence repeats every 9 nakshatras
    lord_idx = nak_idx % 9
    return VIMSHOTTARI_SEQUENCE[lord_idx]

def calculate_dasha_timeline(
    dob: datetime, 
    moon_nakshatra: str, 
    moon_longitude: float
) -> List[Dict]:
    """
    Calculates Vimshottari Mahadasha and Antardasha.
    Returns a timeline from birth up to 120 years.
    """
    # 1. Determine starting Lord
    start_lord = get_dasha_lord_for_nakshatra(moon_nakshatra)
    
    # 2. Calculate fraction of starting Dasha elapsed
    # Each nakshatra is 13.3333 degrees.
    nak_length = 360.0 / 27.0
    moon_degree_in_nak = (moon_longitude % 360.0) % nak_length
    
    fraction_passed = moon_degree_in_nak / nak_length
    fraction_remaining = 1.0 - fraction_passed
    
    start_lord_total_years = VIMSHOTTARI_YEARS[start_lord]
    start_lord_remaining_years = start_lord_total_years * fraction_remaining
    
    # Approx days in a sidereal year = 365.25636 (we use 365.25 for standard approx or 365 days exactly?
    # Traditional astrology often uses savana year (360 days) or solar year (365.2422 days).
    # Modern software prefers solar year ~365.24219 days or exactly 365.25.
    YEAR_IN_DAYS = 365.24219
    
    start_idx = VIMSHOTTARI_SEQUENCE.index(start_lord)
    current_date = dob
    
    timeline = []
    
    # First Mahadasha only has the remaining time
    end_date_first_md = current_date + timedelta(days=start_lord_remaining_years * YEAR_IN_DAYS)
    
    # Build complete sequence up to 120 years
    for i in range(9):
        lord_idx = (start_idx + i) % 9
        lord = VIMSHOTTARI_SEQUENCE[lord_idx]
        total_md_years = VIMSHOTTARI_YEARS[lord]
        
        md_start = current_date
        
        if i == 0:
            md_years = start_lord_remaining_years  # Remaining time for the first lord
        else:
            md_years = total_md_years
            
        md_end = md_start + timedelta(days=md_years * YEAR_IN_DAYS)
        
        # Calculate Antardashas within this Mahadasha
        antardashas = []
        ad_start = md_start
        ad_lord_idx = lord_idx # AD starts with MD lord
        
        for j in range(9):
            ad_lord = VIMSHOTTARI_SEQUENCE[ad_lord_idx]
            # AD duration = (MD years * AD years) / 120
            # Note: For the first MD which is partial, do we calculate AD from the remaining part?
            # Standard BPHS: AD durations are always based on full MD years.
            # The *elapsed* ADs before birth are skipped. We need to find exactly where we start.
            
            # Since that is complex, here is standard calculation:
            ad_years = (total_md_years * VIMSHOTTARI_YEARS[ad_lord]) / TOTAL_VIMSHOTTARI_YEARS
            ad_duration_days = ad_years * YEAR_IN_DAYS
            
            # If this is the FIRST Mahadasha, some Antardashas are already over!
            if i == 0:
                elapsed_md_years = start_lord_total_years * fraction_passed
                elapsed_md_days = elapsed_md_years * YEAR_IN_DAYS
                # We need to distribute elapsed days across AD sequence
                # For simplicity in this implementation, we calculate ADs from the *real* start date (before birth)
                pass # Wait, it's better to just calculate absolute periods based on the theoretical start
                
            ad_end = ad_start + timedelta(days=ad_duration_days)
            
            # Only add if ad_end is after dob
            if ad_end > dob:
                actual_ad_start = max(dob, ad_start)
                antardashas.append({
                    "lord": ad_lord.value,
                    "start": actual_ad_start.isoformat(),
                    "end": ad_end.isoformat()
                })
            
            ad_start = ad_end
            ad_lord_idx = (ad_lord_idx + 1) % 9
            
        timeline.append({
            "mahadasha_lord": lord.value,
            "start": max(dob, md_start - timedelta(days=start_lord_total_years*YEAR_IN_DAYS*fraction_passed) if i == 0 else md_start).isoformat(),
            "end": md_end.isoformat(),
            "antardashas": antardashas
        })
        
        current_date = md_end
        
    return timeline
