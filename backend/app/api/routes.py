from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from app.config import settings
from app.models.schemas import (
    AccuracyAnalysisResponse,
    ForecastExplorerResponse,
    HealthCheckResponse,
    OverviewResponse,
    RecordsResponse,
)
from app.services.analysis_service import AnalysisService
from app.services.elexon_client import ElexonClientException
from app.utils.validation import parse_and_validate_cutoff, parse_and_validate_date, validate_date_range

router = APIRouter()


def get_analysis_service() -> AnalysisService:
    return AnalysisService()


@router.get("/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check():
    """Application and upstream dependency health status."""
    return HealthCheckResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version="1.0.0",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        upstream_elexon_status="connected",
        cache_status="active" if settings.CACHE_ENABLED else "disabled",
    )


@router.get("/analysis/overview", response_model=OverviewResponse, tags=["Analysis"])
async def get_overview(
    decision_date: str = Query("2026-01-10", description="Decision date YYYY-MM-DD (e.g. 2026-01-10)"),
    cutoff_time: str = Query(settings.DEFAULT_CUTOFF_TIME, description="Cutoff time in Europe/London (HH:MM)"),
    matching_mode: str = Query("exact", pattern="^(exact|mapped_hourly)$", description="Matching mode: 'exact' or 'mapped_hourly'"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Overview metrics and quality indicators for a selected decision date and cutoff time.
    Delivery occurs on the day following the decision date.
    """
    valid_date = parse_and_validate_date(decision_date, "decision_date")
    valid_cutoff = parse_and_validate_cutoff(cutoff_time)
    
    try:
        return await service.get_overview(valid_date, valid_cutoff, matching_mode)
    except ElexonClientException as e:
        raise HTTPException(status_code=502, detail=f"Elexon upstream error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis calculation error: {str(e)}")


@router.get("/analysis/forecast", response_model=ForecastExplorerResponse, tags=["Analysis"])
async def get_forecast(
    decision_date: str = Query("2026-01-10", description="Decision date YYYY-MM-DD"),
    cutoff_time: str = Query(settings.DEFAULT_CUTOFF_TIME, description="Cutoff time in Europe/London (HH:MM)"),
    matching_mode: str = Query("exact", pattern="^(exact|mapped_hourly)$"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Decision-time forecast explorer records and selection provenance.
    """
    valid_date = parse_and_validate_date(decision_date, "decision_date")
    valid_cutoff = parse_and_validate_cutoff(cutoff_time)
    
    try:
        return await service.get_forecast_explorer(valid_date, valid_cutoff, matching_mode)
    except ElexonClientException as e:
        raise HTTPException(status_code=502, detail=f"Elexon upstream error: {e.message}")


@router.get("/analysis/records", response_model=RecordsResponse, tags=["Analysis"])
async def get_records(
    decision_date: str = Query("2026-01-10", description="Decision date YYYY-MM-DD"),
    cutoff_time: str = Query(settings.DEFAULT_CUTOFF_TIME, description="Cutoff time in Europe/London (HH:MM)"),
    matching_mode: str = Query("exact", pattern="^(exact|mapped_hourly)$"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Matched forecast and actual records, errors, and quality flags for each delivery period.
    """
    valid_date = parse_and_validate_date(decision_date, "decision_date")
    valid_cutoff = parse_and_validate_cutoff(cutoff_time)
    
    try:
        return await service.get_records(valid_date, valid_cutoff, matching_mode)
    except ElexonClientException as e:
        raise HTTPException(status_code=502, detail=f"Elexon upstream error: {e.message}")


@router.get("/analysis/accuracy", response_model=AccuracyAnalysisResponse, tags=["Analysis"])
async def get_accuracy(
    start_date: str = Query("2026-01-01", description="Start decision date YYYY-MM-DD"),
    end_date: str = Query("2026-01-31", description="End decision date YYYY-MM-DD"),
    cutoff_time: str = Query(settings.DEFAULT_CUTOFF_TIME, description="Cutoff time in Europe/London (HH:MM)"),
    matching_mode: str = Query("exact", pattern="^(exact|mapped_hourly)$"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Aggregate forecast accuracy metrics and daily trends over a date range.
    """
    v_start = parse_and_validate_date(start_date, "start_date")
    v_end = parse_and_validate_date(end_date, "end_date")
    validate_date_range(v_start, v_end)
    valid_cutoff = parse_and_validate_cutoff(cutoff_time)
    
    try:
        return await service.get_accuracy_analysis(v_start, v_end, valid_cutoff, matching_mode)
    except ElexonClientException as e:
        raise HTTPException(status_code=502, detail=f"Elexon upstream error: {e.message}")


@router.get("/analysis/export", tags=["Analysis"])
async def export_csv(
    decision_date: str = Query("2026-01-10", description="Decision date YYYY-MM-DD"),
    cutoff_time: str = Query(settings.DEFAULT_CUTOFF_TIME, description="Cutoff time in Europe/London (HH:MM)"),
    matching_mode: str = Query("exact", pattern="^(exact|mapped_hourly)$"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Generate reproducible CSV export for selected decision analysis.
    """
    valid_date = parse_and_validate_date(decision_date, "decision_date")
    valid_cutoff = parse_and_validate_cutoff(cutoff_time)
    
    try:
        csv_data = await service.generate_csv_export(valid_date, valid_cutoff, matching_mode)
        filename = f"windscope_{valid_date.isoformat()}_{valid_cutoff.replace(':', '')}_{matching_mode}.csv"
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ElexonClientException as e:
        raise HTTPException(status_code=502, detail=f"Elexon upstream error: {e.message}")
