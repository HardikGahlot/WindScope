import csv
import io
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple
from app.config import settings
from app.models.schemas import (
    AccuracyAnalysisResponse,
    DailyTrendItem,
    DecisionTimeForecastRecord,
    ForecastExplorerResponse,
    MatchedDeliveryRecord,
    OverviewResponse,
    RecordsResponse,
)
from app.services.accuracy_metrics import compute_metrics
from app.services.elexon_client import ElexonClient
from app.services.forecast_selection import match_forecast_with_actuals, select_decision_time_forecasts
from app.utils.datetime_utils import (
    compute_cutoff_datetime_utc,
    format_iso_utc,
    get_expected_settlement_periods_for_date,
    to_london_display,
)


class AnalysisService:
    def __init__(self, client: Optional[ElexonClient] = None):
        self.client = client or ElexonClient()

    async def _fetch_and_prepare_day_data(
        self,
        decision_date: date,
        cutoff_time_str: str,
        matching_mode: str = "exact",
    ) -> Tuple[date, List[DecisionTimeForecastRecord], List[MatchedDeliveryRecord]]:
        delivery_date = decision_date + timedelta(days=1)
        
        # Determine WINDFOR query window:
        # Include publications from start of prior day up to end of decision date
        pub_from = datetime.combine(decision_date - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        pub_to = datetime.combine(decision_date, datetime.max.time(), tzinfo=timezone.utc)
        
        # Parallel or sequential fetch of WINDFOR and FUELHH
        windfor_records = await self.client.get_forecast_wind_generation(pub_from, pub_to)
        fuelhh_records = await self.client.get_actual_wind_generation(delivery_date, delivery_date)
        
        # Run forecast selection algorithm
        selected_forecasts = select_decision_time_forecasts(
            windfor_records=windfor_records,
            decision_date=decision_date,
            delivery_date=delivery_date,
            cutoff_time_str=cutoff_time_str,
            matching_mode=matching_mode,
        )
        
        # Match with actuals
        matched_records = match_forecast_with_actuals(
            selected_forecasts=selected_forecasts,
            actual_records=fuelhh_records,
            delivery_date=delivery_date,
            cutoff_time_str=cutoff_time_str,
        )
        
        return delivery_date, selected_forecasts, matched_records

    async def get_overview(
        self,
        decision_date: date,
        cutoff_time_str: str,
        matching_mode: str = "exact",
    ) -> OverviewResponse:
        delivery_date, forecasts, matched = await self._fetch_and_prepare_day_data(
            decision_date, cutoff_time_str, matching_mode
        )
        
        cutoff_dt_utc = compute_cutoff_datetime_utc(decision_date, cutoff_time_str)
        expected_periods = get_expected_settlement_periods_for_date(delivery_date)
        total_expected = len(expected_periods)
        
        metrics = compute_metrics(matched, total_expected)
        
        # Compute generation averages and peaks
        valid_f = [m.forecast_generation_mw for m in matched if m.forecast_generation_mw is not None]
        valid_a = [m.actual_generation_mw for m in matched if m.actual_generation_mw is not None]
        
        expected_avg = round(sum(valid_f) / len(valid_f), 2) if valid_f else None
        expected_peak = round(max(valid_f), 2) if valid_f else None
        actual_avg = round(sum(valid_a) / len(valid_a), 2) if valid_a else None
        actual_peak = round(max(valid_a), 2) if valid_a else None
        
        # Find latest eligible publish time among selected forecasts
        pub_times_utc = [m.publish_time_utc for m in matched if m.publish_time_utc]
        latest_pub_utc = max(pub_times_utc) if pub_times_utc else None
        latest_pub_london = None
        if latest_pub_utc:
            from app.utils.datetime_utils import parse_iso_utc
            latest_pub_london = to_london_display(parse_iso_utc(latest_pub_utc))
            
        notes = [
            f"Evaluated decision date {decision_date.isoformat()} for delivery date {delivery_date.isoformat()}.",
            f"Configured cutoff: {cutoff_time_str} Europe/London ({format_iso_utc(cutoff_dt_utc)} UTC). Assumption for demonstration.",
            "Wind forecast error alone does not determine net purchase volumes (demand and other sources excluded).",
            "Data source: National Elexon BMRS API (FUELHH and WINDFOR streams).",
        ]
        if matching_mode == "exact":
            notes.append("Strict exact matching: 24 hourly periods matched; 24 half-hourly (:30) periods transparently marked missing.")
        else:
            notes.append("Mapped hourly matching: Hourly forecasts mapped across both half-hour settlement periods.")
            
        return OverviewResponse(
            product_name=settings.PROJECT_NAME,
            decision_date=decision_date.isoformat(),
            delivery_date=delivery_date.isoformat(),
            decision_cutoff_london=f"{cutoff_time_str} Europe/London",
            decision_cutoff_utc=format_iso_utc(cutoff_dt_utc),
            latest_eligible_publish_time_utc=latest_pub_utc,
            latest_eligible_publish_time_london=latest_pub_london,
            expected_wind_generation_avg_mw=expected_avg,
            actual_wind_generation_avg_mw=actual_avg,
            expected_wind_generation_peak_mw=expected_peak,
            actual_wind_generation_peak_mw=actual_peak,
            metrics=metrics,
            data_source="Elexon BMRS (FUELHH & WINDFOR)",
            retrieval_status="success",
            matching_mode=matching_mode,
            notes=notes,
        )

    async def get_forecast_explorer(
        self,
        decision_date: date,
        cutoff_time_str: str,
        matching_mode: str = "exact",
    ) -> ForecastExplorerResponse:
        delivery_date, forecasts, _ = await self._fetch_and_prepare_day_data(
            decision_date, cutoff_time_str, matching_mode
        )
        cutoff_dt_utc = compute_cutoff_datetime_utc(decision_date, cutoff_time_str)
        matched_count = sum(1 for f in forecasts if f.forecast_generation_mw is not None)
        missing_count = sum(1 for f in forecasts if f.forecast_generation_mw is None)
        
        return ForecastExplorerResponse(
            decision_date=decision_date.isoformat(),
            delivery_date=delivery_date.isoformat(),
            decision_cutoff_london=f"{cutoff_time_str} Europe/London",
            decision_cutoff_utc=format_iso_utc(cutoff_dt_utc),
            total_delivery_periods=len(forecasts),
            matched_forecasts_count=matched_count,
            missing_forecasts_count=missing_count,
            matching_mode=matching_mode,
            records=forecasts,
        )

    async def get_records(
        self,
        decision_date: date,
        cutoff_time_str: str,
        matching_mode: str = "exact",
    ) -> RecordsResponse:
        delivery_date, _, matched = await self._fetch_and_prepare_day_data(
            decision_date, cutoff_time_str, matching_mode
        )
        matched_count = sum(1 for m in matched if m.match_status == "matched")
        missing_f = sum(1 for m in matched if m.forecast_generation_mw is None)
        missing_a = sum(1 for m in matched if m.actual_generation_mw is None)
        
        return RecordsResponse(
            decision_date=decision_date.isoformat(),
            delivery_date=delivery_date.isoformat(),
            decision_cutoff_london=f"{cutoff_time_str} Europe/London",
            total_records=len(matched),
            matched_records=matched_count,
            missing_forecasts=missing_f,
            missing_actuals=missing_a,
            matching_mode=matching_mode,
            records=matched,
        )

    async def get_accuracy_analysis(
        self,
        start_date: date,
        end_date: date,
        cutoff_time_str: str,
        matching_mode: str = "exact",
    ) -> AccuracyAnalysisResponse:
        all_matched_records: List[MatchedDeliveryRecord] = []
        daily_trends: List[DailyTrendItem] = []
        total_expected_sum = 0
        
        current = start_date
        while current <= end_date:
            try:
                delivery_date, _, matched = await self._fetch_and_prepare_day_data(
                    current, cutoff_time_str, matching_mode
                )
                expected_p = len(get_expected_settlement_periods_for_date(delivery_date))
                total_expected_sum += expected_p
                all_matched_records.extend(matched)
                
                day_metric = compute_metrics(matched, expected_p)
                valid_f = [m.forecast_generation_mw for m in matched if m.forecast_generation_mw is not None]
                valid_a = [m.actual_generation_mw for m in matched if m.actual_generation_mw is not None]
                
                daily_trends.append(
                    DailyTrendItem(
                        decision_date=current.isoformat(),
                        delivery_date=delivery_date.isoformat(),
                        mae=day_metric.mae,
                        rmse=day_metric.rmse,
                        bias=day_metric.bias,
                        mape=day_metric.mape,
                        avg_forecast_mw=round(sum(valid_f) / len(valid_f), 2) if valid_f else None,
                        avg_actual_mw=round(sum(valid_a) / len(valid_a), 2) if valid_a else None,
                        matched_periods=day_metric.matched_periods_count,
                        total_expected=expected_p,
                        coverage_percentage=day_metric.coverage_percentage,
                    )
                )
            except Exception as e:
                # Log and continue with other days
                pass
            current += timedelta(days=1)
            
        aggregate_metrics = compute_metrics(all_matched_records, total_expected_sum)
        
        # Sort for largest absolute errors
        valid_matched = [r for r in all_matched_records if r.abs_error_mw is not None]
        valid_matched.sort(key=lambda r: r.abs_error_mw or 0.0, reverse=True)
        largest_errors = valid_matched[:10]
        
        return AccuracyAnalysisResponse(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            decision_cutoff_london=f"{cutoff_time_str} Europe/London",
            aggregate_metrics=aggregate_metrics,
            daily_trends=daily_trends,
            largest_errors=largest_errors,
            notes=[
                f"Aggregated across {len(daily_trends)} decision days ({start_date.isoformat()} to {end_date.isoformat()}).",
                "Error defined as F - A (positive: overforecast, negative: underforecast).",
                "MAPE excludes zero actual values and reports exclusion counts.",
            ],
        )

    async def generate_csv_export(
        self,
        decision_date: date,
        cutoff_time_str: str,
        matching_mode: str = "exact",
    ) -> str:
        delivery_date, _, matched = await self._fetch_and_prepare_day_data(
            decision_date, cutoff_time_str, matching_mode
        )
        
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        
        # Write metadata comments/header
        writer.writerow(["# WindScope UK Wind Forecast Intelligence Export"])
        writer.writerow(["# Decision Date", decision_date.isoformat()])
        writer.writerow(["# Delivery Date", delivery_date.isoformat()])
        writer.writerow(["# Decision Cutoff", f"{cutoff_time_str} Europe/London"])
        writer.writerow(["# Matching Mode", matching_mode])
        writer.writerow(["# Source", "Elexon BMRS (FUELHH, WINDFOR)"])
        writer.writerow(["# Generated At (UTC)", datetime.now(timezone.utc).isoformat()])
        writer.writerow([])
        
        # Columns
        headers = [
            "Settlement Period",
            "Delivery Time UTC",
            "Delivery Time London",
            "Forecast Generation (MW)",
            "Actual Generation (MW)",
            "Forecast Error (MW)",
            "Absolute Error (MW)",
            "Absolute Percentage Error (%)",
            "Forecast Publish Time UTC",
            "Forecast Publish Time London",
            "Decision Cutoff London",
            "Match Status",
            "Quality Flags",
        ]
        writer.writerow(headers)
        
        for r in matched:
            writer.writerow([
                r.settlement_period,
                r.delivery_time_utc,
                r.delivery_time_london,
                f"{r.forecast_generation_mw:.2f}" if r.forecast_generation_mw is not None else "",
                f"{r.actual_generation_mw:.2f}" if r.actual_generation_mw is not None else "",
                f"{r.error_mw:.2f}" if r.error_mw is not None else "",
                f"{r.abs_error_mw:.2f}" if r.abs_error_mw is not None else "",
                f"{r.percentage_error:.2f}" if r.percentage_error is not None else "",
                r.publish_time_utc or "",
                r.publish_time_london or "",
                r.cutoff_time_london,
                r.match_status,
                ";".join(r.data_quality_flags),
            ])
            
        return output.getvalue()
