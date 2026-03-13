from datetime import datetime, date
from app.engine.ephemeris import calculate_chart
from app.engine.karmic_cycles import calculate_all_karmic_cycles
from app.temporal.karmic_timeline import build_karmic_dashboard, get_current_cycle_status

def test_karmic_cycles_detection():
    # Known test case
    dt = datetime(1990, 6, 15, 10, 30)
    # New Delhi
    lat, lon = 28.6139, 77.2090
    asc, planets = calculate_chart(dt, lat, lon)
    
    # Mock payload
    payload = {
        "datetime_utc": "1990-06-15T10:30:00Z",
        "planets": [{"name": p.name.value, "longitude": p.longitude, "sign": p.sign.value} for p in planets]
    }
    
    cycles = calculate_all_karmic_cycles(payload)
    
    # 1. Sade Sati
    sade_satis = cycles.get("sade_sati_cycles", [])
    assert len(sade_satis) >= 2
    for ss in sade_satis:
        assert "start_date" in ss
        assert "peak_start" in ss
        assert "peak_end" in ss
        assert "end_date" in ss
        
    # 2. Saturn Return
    s_returns = cycles.get("saturn_returns", [])
    assert len(s_returns) >= 2
    assert s_returns[0]["number"] == 1
    
    # 3. Jupiter Return
    j_returns = cycles.get("jupiter_returns", [])
    assert len(j_returns) >= 5
    assert j_returns[0]["number"] == 1

def test_karmic_timeline_merging():
    # Mock some data
    mock_cycles = {
        "sade_sati_cycles": [
            {
                "cycle": "sade_sati",
                "start_date": "2025-03",
                "peak_start": "2027-04",
                "peak_end": "2029-07",
                "end_date": "2032-01"
            }
        ],
        "saturn_returns": [
            {
                "number": 1,
                "start": "2034-02",
                "exact": "2034-08",
                "end": "2035-01"
            }
        ],
        "jupiter_returns": [
            {
                "number": 1,
                "year": 2026
            }
        ]
    }
    
    current = date(2026, 6, 15)
    dash = build_karmic_dashboard(mock_cycles, current)
    
    assert "timeline" in dash
    assert dash["sade_sati"]["current_phase"] == "rising"
    assert "cycle_progress" in dash
    assert dash["cycle_progress"]["sade_sati"] > 0
    
    status = get_current_cycle_status(dash, current)
    
    active = [c["cycle"] for c in status["active_cycles"]]
    assert "sade_sati" in active
    assert "jupiter_return" in active
    
    upcoming = [c["cycle"] for c in status["upcoming_cycles"]]
    assert "saturn_return" in upcoming

if __name__ == "__main__":
    print("Running test_karmic_cycles_detection...")
    test_karmic_cycles_detection()
    print("✓ test_karmic_cycles_detection passed")
    
    print("Running test_karmic_timeline_merging...")
    test_karmic_timeline_merging()
    print("✓ test_karmic_timeline_merging passed")
    print("\nALL tests passed!")

