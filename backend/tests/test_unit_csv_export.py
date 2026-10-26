import csv
import io
from datetime import date
import pytest
from app.models.schemas import RawFuelHHRecord, RawWindforRecord
from app.services.analysis_service import AnalysisService
from app.services.elexon_client import ElexonClient


class MockElexonClient(ElexonClient):
    async def get_forecast_wind_generation(self, pub_from, pub_to):
        return [
            RawWindforRecord(publishTime="2026-01-01T08:00:00Z", startTime="2026-01-02T00:00:00Z", generation=15000.0),
            RawWindforRecord(publishTime="2026-01-01T08:00:00Z", startTime="2026-01-02T01:00:00Z", generation=14500.0),
        ]

    async def get_actual_wind_generation(self, s_from, s_to):
        return [
            RawFuelHHRecord(startTime="2026-01-02T00:00:00Z", fuelType="WIND", generation=14800.0),
            RawFuelHHRecord(startTime="2026-01-02T00:30:00Z", fuelType="WIND", generation=14900.0),
            RawFuelHHRecord(startTime="2026-01-02T01:00:00Z", fuelType="WIND", generation=14200.0),
        ]


@pytest.mark.asyncio
async def test_csv_export_format_and_escaping():
    service = AnalysisService(client=MockElexonClient())
    csv_str = await service.generate_csv_export(
        decision_date=date(2026, 1, 1),
        cutoff_time_str="09:30",
        matching_mode="exact",
    )

    # Verify CSV is parseable
    f = io.StringIO(csv_str)
    reader = csv.reader(f)
    rows = list(reader)

    # Check metadata headers
    metadata_lines = [r for r in rows if r and r[0].startswith("#")]
    assert len(metadata_lines) >= 5
    assert any("Decision Date" in r[0] for r in metadata_lines)
    assert any("2026-01-01" in " ".join(r) for r in metadata_lines)

    # Find the data header line
    header_idx = next(i for i, r in enumerate(rows) if r and r[0] == "Settlement Period")
    headers = rows[header_idx]
    assert "Settlement Period" in headers
    assert "Forecast Generation (MW)" in headers
    assert "Actual Generation (MW)" in headers
    assert "Forecast Error (MW)" in headers

    # Verify rows exist after header
    data_rows = rows[header_idx + 1:]
    assert len(data_rows) == 48  # exactly 48 settlement periods for 2026-01-02

    # Check period 1 (00:00:00Z)
    period1 = data_rows[0]
    assert period1[0] == "1"
    assert period1[3] == "15000.00"  # Forecast
    assert period1[4] == "14800.00"  # Actual
    assert period1[5] == "200.00"    # Error: 15000 - 14800
    assert period1[11] == "matched"

    # Check period 2 (00:30:00Z - exact mode has missing forecast)
    period2 = data_rows[1]
    assert period2[0] == "2"
    assert period2[3] == ""  # Missing forecast
    assert period2[4] == "14900.00"  # Actual exists
    assert period2[11] == "missing_forecast"
