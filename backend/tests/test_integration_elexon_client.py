from datetime import date, datetime, timezone
import httpx
import pytest
import respx
from app.services.cache_service import CacheService
from app.services.elexon_client import ElexonClient, ElexonClientException


@pytest.fixture
def clean_cache(tmp_path):
    return CacheService(str(tmp_path / "test_cache"))


@pytest.mark.asyncio
@respx.mock
async def test_successful_fuelhh_retrieval(clean_cache):
    route = respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream").respond(
        status_code=200,
        json=[
            {"dataset": "FUELHH", "startTime": "2026-01-02T00:00:00Z", "fuelType": "WIND", "generation": 10500},
            {"dataset": "FUELHH", "startTime": "2026-01-02T00:00:00Z", "fuelType": "NUCLEAR", "generation": 4500},
            {"dataset": "FUELHH", "startTime": "2026-01-02T00:30:00Z", "fuelType": "WIND", "generation": 10800},
        ],
    )

    client = ElexonClient(cache_service=clean_cache)
    records = await client.get_actual_wind_generation(date(2026, 1, 2), date(2026, 1, 2))

    assert route.called
    assert route.calls.last.request.url.params["settlementDateFrom"] == "2026-01-02"
    assert route.calls.last.request.url.params["fuelType"] == "WIND"
    # NUCLEAR record must be filtered out, leaving exactly 2 WIND records
    assert len(records) == 2
    assert records[0].generation == 10500.0
    assert records[1].generation == 10800.0


@pytest.mark.asyncio
@respx.mock
async def test_successful_windfor_retrieval(clean_cache):
    route = respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream").respond(
        status_code=200,
        json=[
            {"dataset": "WINDFOR", "publishTime": "2026-01-01T09:30:00Z", "startTime": "2026-01-02T00:00:00Z", "generation": 12345},
        ],
    )

    client = ElexonClient(cache_service=clean_cache)
    from_dt = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    to_dt = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    records = await client.get_forecast_wind_generation(from_dt, to_dt)

    assert route.called
    assert len(records) == 1
    assert records[0].generation == 12345.0
    assert records[0].publishTime == "2026-01-01T09:30:00Z"


@pytest.mark.asyncio
@respx.mock
async def test_upstream_timeout_and_retries(clean_cache):
    route = respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream").mock(
        side_effect=httpx.TimeoutException("Connection timed out")
    )

    client = ElexonClient(cache_service=clean_cache)
    client.timeout = 0.5

    with pytest.raises(ElexonClientException) as exc_info:
        await client.get_actual_wind_generation(date(2026, 1, 2), date(2026, 1, 2))

    assert "Failed to fetch data from Elexon API after" in str(exc_info.value)
    assert route.call_count == client.max_retries


@pytest.mark.asyncio
@respx.mock
async def test_upstream_500_server_error_retries(clean_cache):
    route = respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream").respond(
        status_code=500,
        text="Internal Server Error",
    )

    client = ElexonClient(cache_service=clean_cache)
    from_dt = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    to_dt = datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc)

    with pytest.raises(ElexonClientException):
        await client.get_forecast_wind_generation(from_dt, to_dt)

    assert route.call_count == client.max_retries


@pytest.mark.asyncio
@respx.mock
async def test_invalid_response_structure_handling(clean_cache):
    respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream").respond(
        status_code=200,
        text="<html><body>Gateway Error</body></html>",
    )

    client = ElexonClient(cache_service=clean_cache)
    with pytest.raises(ElexonClientException) as exc_info:
        await client.get_actual_wind_generation(date(2026, 1, 2), date(2026, 1, 2))

    assert "Malformed JSON" in str(exc_info.value)
