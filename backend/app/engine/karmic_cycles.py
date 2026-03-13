import swisseph as swe
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Any

from app.engine.ephemeris import (
    get_julian_day, 
    SWE_PLANETS, 
    swe, 
    ZODIAC_SIGNS, 
    get_sign_info
)
from app.engine.models import PlanetName


def _calculate_planet_transit_month_by_month(
    birth_date: datetime, 
    years_to_scan: int, 
    planet: PlanetName
) -> List[Dict[str, Any]]:
    """
    Pre-calculates a planet's sign and longitude for the 1st of every month
    for a given number of years.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    swe_id = SWE_PLANETS[planet]
    
    timeline = []
    current_date = datetime(birth_date.year, birth_date.month, 1, tzinfo=birth_date.tzinfo)
    end_date = current_date + relativedelta(years=years_to_scan)
    
    while current_date <= end_date:
        jd = get_julian_day(current_date)
        res, _ = swe.calc_ut(jd, swe_id, flags)
        lon = res[0]
        sign, deg = get_sign_info(lon)
        sign_idx = ZODIAC_SIGNS.index(sign)
        
        timeline.append({
            "date": current_date,
            "year": current_date.year,
            "month": current_date.month,
            "period_str": f"{current_date.year}-{current_date.month:02d}",
            "longitude": lon,
            "sign_idx": sign_idx
        })
        current_date += relativedelta(months=1)
        
    return timeline


def get_sade_sati_cycles(birth_date: datetime, natal_moon_sign_idx: int) -> List[Dict[str, Any]]:
    """
    Detects Sade Sati cycles (Saturn transiting 1 sign before, same sign, 1 sign after Moon).
    """
    saturn_timeline = _calculate_planet_transit_month_by_month(birth_date, 100, PlanetName.SATURN)
    
    rising_sign = (natal_moon_sign_idx - 1) % 12
    peak_sign = natal_moon_sign_idx
    setting_sign = (natal_moon_sign_idx + 1) % 12
    sade_sati_signs = [rising_sign, peak_sign, setting_sign]
    
    cycles = []
    current_cycle = None
    
    for month_data in saturn_timeline:
        sign = month_data["sign_idx"]
        period = month_data["period_str"]
        
        if sign in sade_sati_signs:
            if not current_cycle:
                current_cycle = {
                    "start_date": period,
                    "peak_start": None,
                    "peak_end": None,
                    "end_date": period,
                    "months_in_peak": []
                }
            current_cycle["end_date"] = period
            
            if sign == peak_sign:
                if not current_cycle["peak_start"]:
                    current_cycle["peak_start"] = period
                current_cycle["months_in_peak"].append(period)
                current_cycle["peak_end"] = period
        else:
            if current_cycle:
                # Cycle ended
                # Ensure it's a valid cycle (at least some months long, covering peak)
                if current_cycle["peak_start"]:
                    cycles.append({
                        "cycle": "sade_sati",
                        "start_date": current_cycle["start_date"],
                        "peak_start": current_cycle["peak_start"],
                        "peak_end": current_cycle["peak_end"],
                        "end_date": current_cycle["end_date"]
                    })
                current_cycle = None
                
    # Close any active cycle at the end of the timeline
    if current_cycle and current_cycle["peak_start"]:
        cycles.append({
            "cycle": "sade_sati",
            "start_date": current_cycle["start_date"],
            "peak_start": current_cycle["peak_start"],
            "peak_end": current_cycle["peak_end"],
            "end_date": current_cycle["end_date"]
        })
        
    return cycles


def get_saturn_returns(birth_date: datetime, natal_saturn_lon: float) -> List[Dict[str, Any]]:
    """
    Detects Saturn Return cycles.
    Influence window: when Saturn is in the same sign as natal Saturn.
    Exact: when longitude is closest to natal longitude.
    """
    saturn_timeline = _calculate_planet_transit_month_by_month(birth_date, 100, PlanetName.SATURN)
    natal_sign_idx, _ = get_sign_info(natal_saturn_lon)
    natal_sign_idx = ZODIAC_SIGNS.index(natal_sign_idx)
    
    returns = []
    current_return = None
    return_number = 1
    
    for i, month_data in enumerate(saturn_timeline):
        # Skip the first few years to avoid detecting birth as a return
        if month_data["year"] - birth_date.year < 20:
            continue
            
        sign = month_data["sign_idx"]
        period = month_data["period_str"]
        
        if sign == natal_sign_idx:
            if not current_return:
                current_return = {
                    "number": return_number,
                    "start": period,
                    "end": period,
                    "closest_diff": float('inf'),
                    "exact": period
                }
            
            current_return["end"] = period
            
            # Find closest longitude
            diff = abs(month_data["longitude"] - natal_saturn_lon)
            if diff < current_return["closest_diff"]:
                current_return["closest_diff"] = diff
                current_return["exact"] = period
                
        else:
            if current_return:
                del current_return["closest_diff"]
                returns.append(current_return)
                return_number += 1
                current_return = None
                
    if current_return:
        del current_return["closest_diff"]
        returns.append(current_return)

    return returns


def get_jupiter_returns(birth_date: datetime, natal_jupiter_lon: float) -> List[Dict[str, Any]]:
    """
    Detects Jupiter Return cycles. ~12 year intervals.
    """
    jupiter_timeline = _calculate_planet_transit_month_by_month(birth_date, 100, PlanetName.JUPITER)
    natal_sign_idx, _ = get_sign_info(natal_jupiter_lon)
    natal_sign_idx = ZODIAC_SIGNS.index(natal_sign_idx)
    
    returns = []
    current_return = None
    return_number = 1
    
    for month_data in jupiter_timeline:
        # Skip first few years
        if month_data["year"] - birth_date.year < 5:
            continue
            
        sign = month_data["sign_idx"]
        
        if sign == natal_sign_idx:
            if not current_return:
                current_return = {
                    "number": return_number,
                    "year": month_data["year"],
                    "closest_diff": float('inf')
                }
            
            diff = abs(month_data["longitude"] - natal_jupiter_lon)
            if diff < current_return["closest_diff"]:
                current_return["closest_diff"] = diff
                current_return["year"] = month_data["year"]
        else:
            if current_return:
                del current_return["closest_diff"]
                returns.append(current_return)
                return_number += 1
                current_return = None
                
    if current_return:
        del current_return["closest_diff"]
        returns.append(current_return)

    return returns

def calculate_all_karmic_cycles(natal_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Master function to compute all karmic cycles for a given chart payload.
    """
    dt_str = natal_payload["datetime_utc"]
    # Handle ISO format parsing which might have 'Z'
    dt_str = dt_str.replace("Z", "+00:00")
    birth_date = datetime.fromisoformat(dt_str)
    
    planets = natal_payload.get("planets", [])
    
    moon = next((p for p in planets if p["name"] == PlanetName.MOON.value), None)
    saturn = next((p for p in planets if p["name"] == PlanetName.SATURN.value), None)
    jupiter = next((p for p in planets if p["name"] == PlanetName.JUPITER.value), None)
    
    sade_satis = []
    if moon:
        moon_sign_idx = ZODIAC_SIGNS.index(moon["sign"])
        sade_satis = get_sade_sati_cycles(birth_date, moon_sign_idx)
        
    saturn_returns = []
    if saturn:
        saturn_returns = get_saturn_returns(birth_date, saturn["longitude"])
        
    jupiter_returns = []
    if jupiter:
        jupiter_returns = get_jupiter_returns(birth_date, jupiter["longitude"])
        
    # Standardize the Sade Sati return format to match requirement 
    # { "cycle": "sade_sati", "start_date": "...", ... }
    # but the API response requests:
    # { "sade_sati": { active or latest info }, "saturn_return": [...], ... }
    # We will build that in timeline/status logic.
    
    return {
        "sade_sati_cycles": sade_satis,
        "saturn_returns": saturn_returns,
        "jupiter_returns": jupiter_returns
    }
