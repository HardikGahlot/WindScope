import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, List, Optional
from app.models.schemas import RawFuelHHRecord, RawWindforRecord
from app.utils.datetime_utils import format_iso_utc, parse_iso_utc


import json
import os
import shutil
import sqlite3
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, List, Optional
from app.models.schemas import RawFuelHHRecord, RawWindforRecord
from app.utils.datetime_utils import format_iso_utc, parse_iso_utc


class CacheService:
    def __init__(self, cache_dir: str):
        original_cache_dir = Path(cache_dir)
        original_db = original_cache_dir / "bmrs_cache.db"
        
        # Detect serverless / read-only environment (e.g. Vercel, AWS Lambda)
        is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
        is_writable = os.access(original_cache_dir, os.W_OK) if original_cache_dir.exists() else True

        if is_serverless or not is_writable:
            # In serverless environments, bundle files are read-only.
            # Copy preloaded database to writable /tmp directory to allow SQLite locks.
            tmp_dir = Path(tempfile.gettempdir()) / "windscope_cache"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            self.cache_dir = tmp_dir
            self.db_path = tmp_dir / "bmrs_cache.db"
            if original_db.exists():
                if not self.db_path.exists() or self.db_path.stat().st_size < original_db.stat().st_size:
                    shutil.copyfile(original_db, self.db_path)
            self._source_cache_dir = original_cache_dir
        else:
            self.cache_dir = original_cache_dir
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = self.cache_dir / "bmrs_cache.db"
            self._source_cache_dir = original_cache_dir

        self._memory_cache: dict = {}
        self._init_db()
        self._import_existing_json_files()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fuelhh (
                    start_time TEXT,
                    settlement_date TEXT,
                    settlement_period INTEGER,
                    fuel_type TEXT,
                    generation REAL,
                    publish_time TEXT,
                    PRIMARY KEY (start_time, fuel_type)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_fuelhh_date ON fuelhh (settlement_date, fuel_type)")
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS windfor (
                    publish_time TEXT,
                    start_time TEXT,
                    generation REAL,
                    PRIMARY KEY (publish_time, start_time)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_windfor_pub ON windfor (publish_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_windfor_start ON windfor (start_time)")
            conn.commit()

    def _import_existing_json_files(self) -> None:
        """Import preloaded json cache files if present and database is empty."""
        with self._get_connection() as conn:
            fuel_count = conn.execute("SELECT COUNT(*) FROM fuelhh").fetchone()[0]
            wind_count = conn.execute("SELECT COUNT(*) FROM windfor").fetchone()[0]
            
            source_dir = getattr(self, "_source_cache_dir", self.cache_dir)
            if fuel_count == 0:
                for fpath in list(self.cache_dir.glob("fuelhh_*.json")) + list(source_dir.glob("fuelhh_*.json")):
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            items = json.load(f)
                            for it in items:
                                if it.get("fuelType") == "WIND":
                                    conn.execute(
                                        "INSERT OR IGNORE INTO fuelhh VALUES (?, ?, ?, ?, ?, ?)",
                                        (it["startTime"], it.get("settlementDate"), it.get("settlementPeriod"), "WIND", it.get("generation"), it.get("publishTime")),
                                    )
                    except Exception:
                        pass

            if wind_count == 0:
                for fpath in list(self.cache_dir.glob("windfor_*.json")) + list(source_dir.glob("windfor_*.json")):
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            items = json.load(f)
                            for it in items:
                                conn.execute(
                                    "INSERT OR IGNORE INTO windfor VALUES (?, ?, ?)",
                                    (it["publishTime"], it["startTime"], it.get("generation")),
                                )
                    except Exception:
                        pass
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        return self._memory_cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self._memory_cache[key] = value

    # FUELHH methods
    def get_fuelhh_wind_records(self, date_from: date, date_to: date) -> Optional[List[RawFuelHHRecord]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT start_time, settlement_date, settlement_period, fuel_type, generation, publish_time
                FROM fuelhh
                WHERE settlement_date >= ? AND settlement_date <= ? AND fuel_type = 'WIND'
                ORDER BY start_time ASC
                """,
                (date_from.isoformat(), date_to.isoformat()),
            ).fetchall()
            
            if not rows:
                return None
            
            num_days = (date_to - date_from).days + 1
            if len(rows) < num_days * 46:
                return None
                
            return [
                RawFuelHHRecord(
                    dataset="FUELHH",
                    publishTime=r["publish_time"],
                    startTime=r["start_time"],
                    settlementDate=r["settlement_date"],
                    settlementPeriod=r["settlement_period"],
                    fuelType="WIND",
                    generation=r["generation"],
                )
                for r in rows
            ]

    def store_fuelhh_records(self, records: List[RawFuelHHRecord]) -> None:
        with self._get_connection() as conn:
            for r in records:
                if r.fuelType == "WIND":
                    conn.execute(
                        "INSERT OR REPLACE INTO fuelhh VALUES (?, ?, ?, ?, ?, ?)",
                        (r.startTime, r.settlementDate, r.settlementPeriod, "WIND", r.generation, r.publishTime),
                    )
            conn.commit()

    # WINDFOR methods
    def get_windfor_records(self, pub_from: datetime, pub_to: datetime) -> Optional[List[RawWindforRecord]]:
        from_str = format_iso_utc(pub_from)
        to_str = format_iso_utc(pub_to)
        
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT publish_time, start_time, generation
                FROM windfor
                WHERE publish_time >= ? AND publish_time <= ?
                ORDER BY publish_time ASC, start_time ASC
                """,
                (from_str, to_str),
            ).fetchall()
            
            if not rows:
                return None
            
            return [
                RawWindforRecord(
                    dataset="WINDFOR",
                    publishTime=r["publish_time"],
                    startTime=r["start_time"],
                    generation=r["generation"],
                )
                for r in rows
            ]

    def store_windfor_records(self, records: List[RawWindforRecord]) -> None:
        with self._get_connection() as conn:
            for r in records:
                conn.execute(
                    "INSERT OR REPLACE INTO windfor VALUES (?, ?, ?)",
                    (r.publishTime, r.startTime, r.generation),
                )
            conn.commit()
