import sys
sys.path.append('backend')
from app.api.endpoints import generate_chart, ChartRequest
from datetime import datetime
req = ChartRequest(name="Test", gender="Male", datetime_utc=datetime.now(), latitude=28.6, longitude=77.2)
try:
    generate_chart(req)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
