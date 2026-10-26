import pytest
from fastapi.testclient import TestClient
from app.api.routes import get_analysis_service
from app.main import app
from app.models.schemas import RawFuelHHRecord, RawWindforRecord
from app.services.analysis_service import AnalysisService
from app.services.elexon_client import ElexonClient


class FakeElexonClient(ElexonClient):
    async def get_forecast_wind_generation(self, pub_from, pub_to):
        return [
            RawWindforRecord(publishTime="2026-01-01T08:00:00Z", startTime="2026-01-02T12:00:00Z", generation=16000.0),
        ]

    async def get_actual_wind_generation(self, s_from, s_to):
        return [
            RawFuelHHRecord(startTime="2026-01-02T12:00:00Z", fuelType="WIND", generation=15500.0),
        ]


def override_service():
    return AnalysisService(client=FakeElexonClient())


app.dependency_overrides[get_analysis_service] = override_service
client = TestClient(app)


def test_health_check_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "WindScope" in data["service"]


def test_overview_endpoint():
    res = client.get("/api/analysis/overview?decision_date=2026-01-01&cutoff_time=09:30")
    assert res.status_code == 200
    data = res.json()
    assert data["decision_date"] == "2026-01-01"
    assert data["delivery_date"] == "2026-01-02"
    assert data["decision_cutoff_london"] == "09:30 Europe/London"
    assert data["metrics"]["matched_periods_count"] == 1
    assert data["metrics"]["mae"] == 500.0  # 16000 - 15500


def test_forecast_explorer_endpoint():
    res = client.get("/api/analysis/forecast?decision_date=2026-01-01&cutoff_time=09:30")
    assert res.status_code == 200
    data = res.json()
    assert data["total_delivery_periods"] == 48
    assert data["matched_forecasts_count"] == 1


def test_records_endpoint():
    res = client.get("/api/analysis/records?decision_date=2026-01-01&cutoff_time=09:30")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 48
    assert data["matched_records"] == 1


def test_accuracy_endpoint():
    res = client.get("/api/analysis/accuracy?start_date=2026-01-01&end_date=2026-01-02&cutoff_time=09:30")
    assert res.status_code == 200
    data = res.json()
    assert data["start_date"] == "2026-01-01"
    assert data["end_date"] == "2026-01-02"
    assert len(data["daily_trends"]) == 2


def test_csv_export_endpoint():
    res = client.get("/api/analysis/export?decision_date=2026-01-01&cutoff_time=09:30")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in res.headers["content-disposition"]
    assert "Settlement Period" in res.text


def test_invalid_date_validation():
    res = client.get("/api/analysis/overview?decision_date=not-a-date")
    assert res.status_code == 400
    assert "Invalid decision_date format" in res.json()["detail"]


def test_invalid_cutoff_validation():
    res = client.get("/api/analysis/overview?decision_date=2026-01-01&cutoff_time=25:00")
    assert res.status_code == 400
    assert "out of range" in res.json()["detail"]
