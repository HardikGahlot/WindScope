import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
import httpx
from app.config import settings
from app.models.schemas import RawFuelHHRecord, RawWindforRecord
from app.services.cache_service import CacheService
from app.utils.datetime_utils import format_iso_utc, parse_iso_utc

logger = logging.getLogger(__name__)


class ElexonClientException(Exception):
    """Base exception for Elexon BMRS API interactions."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class ElexonClient:
    """
    Dedicated client for Elexon BMRS API endpoints:
    - FUELHH/stream: Half-hourly actual generation by fuel type
    - WINDFOR/stream: Wind generation forecast stream with publication history
    """
    def __init__(self, base_url: Optional[str] = None, cache_service: Optional[CacheService] = None):
        self.base_url = (base_url or settings.ELEXON_BASE_URL).rstrip("/")
        self.cache = cache_service or CacheService(settings.CACHE_DIR)
        self.timeout = settings.HTTP_TIMEOUT_SECONDS
        self.max_retries = settings.HTTP_MAX_RETRIES

    async def _fetch_with_retry(self, url: str, params: dict) -> list:
        headers = {
            "User-Agent": "WindScope-Intelligence-Platform/1.0",
            "Accept": "application/json",
        }
        
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params, headers=headers)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, list):
                                return data
                            elif isinstance(data, dict) and "data" in data:
                                return data["data"]
                            else:
                                return []
                        except Exception as parse_err:
                            raise ElexonClientException(
                                f"Malformed JSON from Elexon API: {str(parse_err)}",
                                status_code=200,
                            )
                    elif response.status_code == 429:
                        # Rate limited
                        wait_sec = 1.0 * (2 ** (attempt - 1))
                        logger.warning(f"Elexon rate limit (429), retrying in {wait_sec}s...")
                        await asyncio.sleep(wait_sec)
                        continue
                    elif 500 <= response.status_code < 600:
                        # Upstream server error, retry
                        wait_sec = 0.5 * attempt
                        logger.warning(f"Elexon 5xx error ({response.status_code}), attempt {attempt}/{self.max_retries}")
                        await asyncio.sleep(wait_sec)
                        continue
                    else:
                        raise ElexonClientException(
                            f"Elexon API returned error status {response.status_code}",
                            status_code=response.status_code,
                            details=response.text[:200],
                        )
            except httpx.TimeoutException as te:
                last_error = te
                logger.warning(f"Timeout connecting to Elexon API on attempt {attempt}/{self.max_retries}")
                await asyncio.sleep(0.5 * attempt)
            except (ElexonClientException, Exception) as ex:
                last_error = ex
                if isinstance(ex, ElexonClientException) and ex.status_code not in (429, 500, 502, 503, 504):
                    raise ex
                logger.warning(f"Error connecting to Elexon: {ex}, attempt {attempt}/{self.max_retries}")
                await asyncio.sleep(0.5 * attempt)
                
        raise ElexonClientException(
            f"Failed to fetch data from Elexon API after {self.max_retries} attempts: {last_error}"
        )

    async def get_actual_wind_generation(
        self,
        settlement_date_from: date,
        settlement_date_to: date,
    ) -> List[RawFuelHHRecord]:
        """
        Fetch actual wind generation records (FUELHH) for the given settlement date range.
        Filters strictly for fuelType == 'WIND'.
        """
        cached = self.cache.get_fuelhh_wind_records(settlement_date_from, settlement_date_to)
        if cached is not None:
            return cached
            
        url = f"{self.base_url}/datasets/FUELHH/stream"
        params = {
            "settlementDateFrom": settlement_date_from.isoformat(),
            "settlementDateTo": settlement_date_to.isoformat(),
            "fuelType": "WIND",
        }
        
        raw_items = await self._fetch_with_retry(url, params)
        records: List[RawFuelHHRecord] = []
        for item in raw_items:
            try:
                # Retain strictly WIND records
                if item.get("fuelType") == "WIND":
                    records.append(RawFuelHHRecord(
                        dataset=item.get("dataset", "FUELHH"),
                        publishTime=item.get("publishTime"),
                        startTime=item["startTime"],
                        settlementDate=item.get("settlementDate"),
                        settlementPeriod=item.get("settlementPeriod"),
                        fuelType="WIND",
                        generation=float(item["generation"]) if item.get("generation") is not None else None,
                    ))
            except Exception:
                continue
                
        # Cache normalized records
        self.cache.store_fuelhh_records(records)
        return records

    async def get_forecast_wind_generation(
        self,
        publish_datetime_from: datetime,
        publish_datetime_to: datetime,
    ) -> List[RawWindforRecord]:
        """
        Fetch historical wind forecast stream (WINDFOR) published within the specified window.
        Preserves all publication versions.
        """
        cached = self.cache.get_windfor_records(publish_datetime_from, publish_datetime_to)
        if cached is not None:
            return cached
            
        from_str = format_iso_utc(publish_datetime_from)
        to_str = format_iso_utc(publish_datetime_to)
        url = f"{self.base_url}/datasets/WINDFOR/stream"
        params = {
            "publishDateTimeFrom": from_str,
            "publishDateTimeTo": to_str,
        }
        
        raw_items = await self._fetch_with_retry(url, params)
        records: List[RawWindforRecord] = []
        for item in raw_items:
            try:
                records.append(RawWindforRecord(
                    dataset=item.get("dataset", "WINDFOR"),
                    publishTime=item["publishTime"],
                    startTime=item["startTime"],
                    generation=float(item["generation"]) if item.get("generation") is not None else None,
                ))
            except Exception:
                continue
                
        self.cache.store_windfor_records(records)
        return records
