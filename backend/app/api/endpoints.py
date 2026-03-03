from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import json

from app.engine.ephemeris import calculate_chart
from app.engine.dasha import calculate_dasha_timeline
from app.engine.yoga import detect_yogas
from app.engine.divisional import get_divisional_charts
from app.engine.models import PlanetName

from app.core.chart_cache import save_chart, load_chart
from app.temporal.period_analysis import analyze_period
from app.temporal.agent import ask_agent
from app.scoring.scorer import score_period

router = APIRouter()

# ─── Models ───────────────────────────────────────────────────────────────────

class ChartRequest(BaseModel):
    name: str
    gender: str
    datetime_utc: datetime
    latitude: float
    longitude: float

class PeriodRequest(BaseModel):
    birth_id: str
    start_date: date
    end_date: date
    domain: Optional[str] = "general"

class AskRequest(BaseModel):
    birth_id: str
    question: str

# ─── /generate-chart ─────────────────────────────────────────────────────────

@router.post("/generate-chart")
def generate_chart(req: ChartRequest):
    # 1. Astro Positions
    ascendant, planets = calculate_chart(
        utc_dt=req.datetime_utc,
        lat=req.latitude,
        lon=req.longitude
    )

    # 2. Moon for Dasha
    moon = next((p for p in planets if p.name == PlanetName.MOON), None)

    # 3. Dasha Timeline
    dashas = []
    if moon:
        dashas = calculate_dasha_timeline(
            dob=req.datetime_utc,
            moon_nakshatra=moon.nakshatra,
            moon_longitude=moon.longitude
        )

    # 4. Yogas
    yogas = detect_yogas(ascendant, planets)

    # 5. Divisional Charts
    div_charts = get_divisional_charts(planets)

    # Serialise everything (Pydantic → dict)
    asc_dict    = json.loads(ascendant.model_dump_json())
    planet_list = [json.loads(p.model_dump_json()) for p in planets]
    div_serialised = {
        d_name: {k: v.value for k, v in mapping.items()}
        for d_name, mapping in div_charts.items()
    }

    payload = {
        "name": req.name,
        "gender": req.gender,
        "datetime_utc": req.datetime_utc.isoformat(),
        "latitude": req.latitude,
        "longitude": req.longitude,
        "ascendant": asc_dict,
        "planets": planet_list,
        "dashas": dashas,
        "yogas": yogas,
        "divisional_charts": div_serialised,
    }

    # 6. Cache and return birth_id
    birth_id = save_chart(payload)

    return {**payload, "birth_id": birth_id}


# ─── /analyze-period ─────────────────────────────────────────────────────────

@router.post("/analyze-period")
def analyze_period_endpoint(req: PeriodRequest):
    natal = load_chart(req.birth_id)
    if not natal:
        raise HTTPException(status_code=404, detail="Chart not found. Please generate chart first.")

    if req.end_date < req.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date.")

    monthly = analyze_period(natal, req.start_date, req.end_date)

    # Score each month
    scored = []
    for m in monthly:
        s = score_period(natal, m, req.domain or "general")
        s["period"]  = m["period"]
        s["month"]   = m["month"]
        s["year"]    = m["year"]
        scored.append(s)

    high_significance = [m for m in monthly if m.get("is_high_significance")]

    return {
        "birth_id":          req.birth_id,
        "domain":            req.domain,
        "period_range":      f"{req.start_date} to {req.end_date}",
        "total_months":      len(monthly),
        "monthly_breakdown": monthly,
        "event_scores":      scored,
        "high_significance_windows": high_significance,
        "summary": {
            "avg_intensity": round(
                sum(m["intensity_index"] for m in monthly) / max(len(monthly), 1), 2
            ),
            "peak_month": max(monthly, key=lambda m: m["intensity_index"])["period"]
            if monthly else None,
            "high_significance_count": len(high_significance),
        },
    }


# ─── /ask ────────────────────────────────────────────────────────────────────

@router.post("/ask")
def ask_endpoint(req: AskRequest):
    natal = load_chart(req.birth_id)
    if not natal:
        raise HTTPException(status_code=404, detail="Chart not found. Please generate chart first.")

    result = ask_agent(question=req.question, natal_payload=natal)
    return result
