import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    getOverview: vi.fn(),
    getRecords: vi.fn(),
    getAccuracy: vi.fn(),
    downloadCsv: vi.fn(),
  },
}));

const mockOverview = {
  product_name: "WindScope — UK Wind Forecast Intelligence",
  decision_date: "2026-01-10",
  delivery_date: "2026-01-11",
  decision_cutoff_london: "09:30 Europe/London",
  decision_cutoff_utc: "2026-01-10T09:30:00Z",
  latest_eligible_publish_time_utc: "2026-01-10T09:30:00Z",
  latest_eligible_publish_time_london: "2026-01-10 09:30 GMT",
  expected_wind_generation_avg_mw: 18454.46,
  actual_wind_generation_avg_mw: 13557.35,
  expected_wind_generation_peak_mw: 20337.0,
  actual_wind_generation_peak_mw: 16018.0,
  metrics: {
    mae: 4948.46,
    rmse: 5020.45,
    bias: 4948.46,
    mape: 38.99,
    total_expected_periods: 48,
    matched_periods_count: 24,
    missing_forecast_count: 24,
    missing_actual_count: 0,
    mape_excluded_zero_actuals_count: 0,
    overforecast_count: 24,
    underforecast_count: 0,
    exact_match_count: 0,
    max_absolute_error_mw: 6215.0,
    coverage_percentage: 50.0,
    calculation_status: "valid",
  },
  data_source: "Elexon BMRS (FUELHH & WINDFOR)",
  retrieval_status: "success",
  matching_mode: "exact" as const,
  notes: [],
};

const mockRecords = {
  decision_date: "2026-01-10",
  delivery_date: "2026-01-11",
  decision_cutoff_london: "09:30 Europe/London",
  total_records: 48,
  matched_records: 24,
  missing_forecasts: 24,
  missing_actuals: 0,
  matching_mode: "exact" as const,
  records: [
    {
      delivery_time_utc: "2026-01-11T00:00:00Z",
      delivery_time_london: "2026-01-11 00:00 GMT",
      settlement_date: "2026-01-11",
      settlement_period: 1,
      forecast_generation_mw: 18000.0,
      actual_generation_mw: 14000.0,
      error_mw: 4000.0,
      abs_error_mw: 4000.0,
      percentage_error: 28.57,
      publish_time_utc: "2026-01-10T09:30:00Z",
      publish_time_london: "2026-01-10 09:30 GMT",
      cutoff_time_london: "09:30 Europe/London",
      match_status: "matched" as const,
      data_quality_flags: [],
    },
    {
      delivery_time_utc: "2026-01-11T00:30:00Z",
      delivery_time_london: "2026-01-11 00:30 GMT",
      settlement_date: "2026-01-11",
      settlement_period: 2,
      forecast_generation_mw: null,
      actual_generation_mw: 14100.0,
      error_mw: null,
      abs_error_mw: null,
      percentage_error: null,
      publish_time_utc: null,
      publish_time_london: null,
      cutoff_time_london: "09:30 Europe/London",
      match_status: "missing_forecast" as const,
      data_quality_flags: ["HOURLY_RESOLUTION_NO_EXACT_HALF_HOUR_FORECAST"],
    },
  ],
};

const mockAccuracy = {
  start_date: "2026-01-01",
  end_date: "2026-01-31",
  decision_cutoff_london: "09:30 Europe/London",
  aggregate_metrics: mockOverview.metrics,
  daily_trends: [
    {
      decision_date: "2026-01-10",
      delivery_date: "2026-01-11",
      mae: 4948.46,
      rmse: 5020.45,
      bias: 4948.46,
      mape: 38.99,
      avg_forecast_mw: 18454.46,
      avg_actual_mw: 13557.35,
      matched_periods: 24,
      total_expected: 48,
      coverage_percentage: 50.0,
    },
  ],
  largest_errors: [],
  notes: [],
};

describe('WindScope Frontend Application', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getOverview as any).mockResolvedValue(mockOverview);
    (api.getRecords as any).mockResolvedValue(mockRecords);
    (api.getAccuracy as any).mockResolvedValue(mockAccuracy);
  });

  it('renders the header and brand identity correctly', async () => {
    render(<App />);
    const headings = screen.getAllByText(/WindScope/i);
    expect(headings.length).toBeGreaterThanOrEqual(1);
    expect(headings[0]).toBeInTheDocument();
    expect(screen.getByText(/UK Wind Forecast Intelligence & BMRS Outturn Accuracy Platform/i)).toBeInTheDocument();
  });

  it('loads and displays overview metrics from API responses', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/Mean Absolute Error/i)).toBeInTheDocument();
      expect(screen.getByText('4,948.46')).toBeInTheDocument();
      expect(screen.getByText(/Mean Forecast Bias/i)).toBeInTheDocument();
      expect(screen.getByText(/Coverage & MAPE/i)).toBeInTheDocument();
    });
  });

  it('displays delivery periods and missing observations transparently', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('SP 1')).toBeInTheDocument();
      expect(screen.getByText('SP 2')).toBeInTheDocument();
      expect(screen.getByText(/Hourly WINDFOR/i)).toBeInTheDocument();
    });
  });

  it('triggers CSV export download upon clicking export button', async () => {
    render(<App />);
    await waitFor(() => {
      const exportBtn = screen.getByRole('button', { name: /Export CSV/i });
      fireEvent.click(exportBtn);
      expect(api.downloadCsv).toHaveBeenCalledWith('2026-01-10', '09:30', 'exact');
    });
  });

  it('opens and closes the methodology modal', async () => {
    render(<App />);
    const methodBtn = screen.getByTitle('Inspect Data Methodology & Formulas');
    fireEvent.click(methodBtn);
    expect(screen.getByText(/WindScope Methodology, Time Semantics & Data Provenance/i)).toBeInTheDocument();

    const closeBtn = screen.getByRole('button', { name: /Close Methodology/i });
    fireEvent.click(closeBtn);
    expect(screen.queryByText(/WindScope Methodology, Time Semantics & Data Provenance/i)).not.toBeInTheDocument();
  });

  it('handles API error state gracefully', async () => {
    (api.getOverview as any).mockRejectedValueOnce(new Error('Network error connecting to Elexon'));
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/Data Retrieval or Processing Error/i)).toBeInTheDocument();
      expect(screen.getByText(/Network error connecting to Elexon/i)).toBeInTheDocument();
    });
  });
});
