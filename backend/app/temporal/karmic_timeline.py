from datetime import datetime, date
from typing import Dict, Any, List

def build_karmic_dashboard(all_cycles: Dict[str, Any], current_date: date) -> Dict[str, Any]:
    """
    Transforms the raw cycle arrays into the structured Dashboard response.
    """
    sade_satis = all_cycles.get("sade_sati_cycles", [])
    saturn_returns = all_cycles.get("saturn_returns", [])
    jupiter_returns = all_cycles.get("jupiter_returns", [])
    
    # 1. Timeline Generator
    timeline_dict: Dict[int, List[str]] = {}
    
    for ss in sade_satis:
        # Add rising
        start_yr = int(ss["start_date"].split("-")[0])
        peak_yr = int(ss["peak_start"].split("-")[0]) if ss.get("peak_start") else start_yr + 2
        peak_end_yr = int(ss["peak_end"].split("-")[0]) if ss.get("peak_end") else peak_yr + 2
        end_yr = int(ss["end_date"].split("-")[0]) if ss.get("end_date") else peak_end_yr + 2
        
        for y in range(start_yr, peak_yr):
            timeline_dict.setdefault(y, []).append("sade_sati_rising")
        for y in range(peak_yr, peak_end_yr + 1):
            timeline_dict.setdefault(y, []).append("sade_sati_peak")
        for y in range(peak_end_yr + 1, end_yr + 1):
            timeline_dict.setdefault(y, []).append("sade_sati_setting")
            
    for sr in saturn_returns:
        yr = int(sr["exact"].split("-")[0])
        timeline_dict.setdefault(yr, []).append("saturn_return")
        
    for jr in jupiter_returns:
        timeline_dict.setdefault(jr["year"], []).append("jupiter_return")

    timeline_arr = []
    for yr in sorted(timeline_dict.keys()):
        # Deduplicate
        cycles = list(set(timeline_dict[yr]))
        timeline_arr.append({
            "year": yr,
            "cycles": cycles
        })

    # 2. Current Cycle Status
    curr_yr_mo = f"{current_date.year}-{current_date.month:02d}"
    curr_yr = current_date.year
    
    active_sade_sati = None
    closest_sade_sati = None
    
    for ss in sade_satis:
        st = ss["start_date"]
        en = ss["end_date"]
        # Find active
        if st <= curr_yr_mo <= en:
            active_sade_sati = dict(ss)
            # Determine phase
            if active_sade_sati.get("peak_start") and active_sade_sati.get("peak_end"):
                if curr_yr_mo < active_sade_sati["peak_start"]:
                    active_sade_sati["current_phase"] = "rising"
                elif curr_yr_mo <= active_sade_sati["peak_end"]:
                    active_sade_sati["current_phase"] = "peak"
                else:
                    active_sade_sati["current_phase"] = "setting"
            else:
                active_sade_sati["current_phase"] = "unknown"
            break
        elif st > curr_yr_mo:
            if not closest_sade_sati:
                closest_sade_sati = ss
                
    if not active_sade_sati and closest_sade_sati:
        active_sade_sati = closest_sade_sati # Return upcoming if none
        
    # 3. Progress metrics
    cycle_progress = {}
    if active_sade_sati and active_sade_sati.get("current_phase"):
        st = datetime.strptime(active_sade_sati["start_date"], "%Y-%m").date()
        en = datetime.strptime(active_sade_sati["end_date"], "%Y-%m").date()
        total_days = (en - st).days
        if total_days > 0 and st <= current_date <= en:
            passed = (current_date - st).days
            cycle_progress["sade_sati"] = round(passed / total_days, 2)
        else:
            cycle_progress["sade_sati"] = 0.0

    return {
        "sade_sati": active_sade_sati,
        "saturn_return": saturn_returns,
        "jupiter_return": jupiter_returns,
        "timeline": timeline_arr,
        "cycle_progress": cycle_progress
    }

def get_current_cycle_status(dashboard_data: Dict[str, Any], current_date: date) -> Dict[str, Any]:
    """
    Extracts the 'current status engine' snapshot for the LLM.
    """
    curr_yr_mo = f"{current_date.year}-{current_date.month:02d}"
    curr_yr = current_date.year
    
    active = []
    upcoming = []
    
    ss = dashboard_data.get("sade_sati")
    if ss:
        if ss.get("start_date", "") <= curr_yr_mo <= ss.get("end_date", ""):
            active.append({
                "cycle": "sade_sati",
                "phase": ss.get("current_phase")
            })
        elif ss.get("start_date", "") > curr_yr_mo:
            upcoming.append({
                "cycle": "sade_sati",
                "start": ss.get("start_date")
            })
            
    for sr in dashboard_data.get("saturn_return", []):
        st = sr.get("start")
        en = sr.get("end")
        if st and en and st <= curr_yr_mo <= en:
            active.append({
                "cycle": "saturn_return",
                "number": sr.get("number")
            })
        elif st and st > curr_yr_mo:
            upcoming.append({
                "cycle": "saturn_return",
                "year": int(st.split("-")[0])
            })
            break # only next
            
    for jr in dashboard_data.get("jupiter_return", []):
        yr = jr.get("year")
        if yr == curr_yr:
            active.append({
                "cycle": "jupiter_return",
                "number": jr.get("number")
            })
        elif yr and yr > curr_yr:
            upcoming.append({
                "cycle": "jupiter_return",
                "year": yr
            })
            break # only next

    return {
        "active_cycles": active,
        "upcoming_cycles": upcoming
    }
