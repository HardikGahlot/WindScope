"""
Preload script to fetch and cache January 2026 historical FUELHH and WINDFOR data from Elexon BMRS API.
Run once to populate the local disk cache: data/cache/
"""
import asyncio
from datetime import date, datetime, timedelta, timezone
from app.config import settings
from app.services.cache_service import CacheService
from app.services.elexon_client import ElexonClient


async def preload():
    print("=== WindScope January 2026 Data Preloader ===")
    cache = CacheService(settings.CACHE_DIR)
    client = ElexonClient(cache_service=cache)
    
    # 1. Fetch FUELHH for 2026-01-01 to 2026-02-02
    start_actual = date(2026, 1, 1)
    end_actual = date(2026, 2, 2)
    print(f"Preloading FUELHH actuals from {start_actual} to {end_actual}...")
    actuals = await client.get_actual_wind_generation(start_actual, end_actual)
    print(f"-> Cached {len(actuals)} FUELHH actual wind records.")
    
    # 2. Fetch WINDFOR for each day in January 2026 in small 3-day chunks
    cur_date = date(2025, 12, 31)
    end_date = date(2026, 2, 1)
    
    print(f"Preloading WINDFOR forecasts from {cur_date} to {end_date}...")
    total_forecasts = 0
    while cur_date < end_date:
        chunk_end = min(cur_date + timedelta(days=3), end_date)
        from_dt = datetime.combine(cur_date, datetime.min.time(), tzinfo=timezone.utc)
        to_dt = datetime.combine(chunk_end, datetime.max.time(), tzinfo=timezone.utc)
        
        print(f"  Fetching WINDFOR chunk: {from_dt.date()} to {to_dt.date()}...")
        try:
            records = await client.get_forecast_wind_generation(from_dt, to_dt)
            total_forecasts += len(records)
            print(f"    -> Received {len(records)} records")
        except Exception as e:
            print(f"    -> Warning fetching chunk: {e}")
            
        cur_date = chunk_end + timedelta(days=1)
        await asyncio.sleep(0.5)  # Respectful pacing
        
    print(f"-> Total WINDFOR records fetched and cached: {total_forecasts}")
    print("Preload complete! Local cache ready in:", settings.CACHE_DIR)


if __name__ == "__main__":
    asyncio.run(preload())
