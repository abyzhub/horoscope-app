import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime, timezone
import swisseph as swe

try:
    from app.engine.ephemeris import calculate_chart
except ImportError as e:
    print("Import Error:", e)
    sys.exit(1)

# Chhatrapati Shivaji Maharaj -> Feb 19, 1630 18:26 (LMT -> UTC approximate)
# Let's just use current date
dt = datetime.now(timezone.utc)
lat = 28.6139 # New Delhi
lon = 77.2090

asc, planets = calculate_chart(dt, lat, lon)
print("Ascendant:", asc.sign, asc.sign_degree, "Nakshatra:", asc.nakshatra, asc.nakshatra_pada)
for p in planets:
    print(f"{p.name.value}: {p.sign.value} {p.sign_degree:.2f}H({p.house}) {p.nakshatra} P{p.nakshatra_pada} R:{p.is_retrograde}")
