import {
  AccuracyAnalysisResponse,
  ForecastExplorerResponse,
  HealthStatus,
  MatchingMode,
  OverviewResponse,
  RecordsResponse,
} from '../types';

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

async function fetchJson<T>(url: string): Promise<T> {
  const fullUrl = API_BASE ? `${API_BASE}${url}` : url;
  const res = await fetch(fullUrl, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      if (errorJson.detail) {
        errorDetail = errorJson.detail;
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return res.json() as Promise<T>;
}

export const api = {
  async getHealth(): Promise<HealthStatus> {
    return fetchJson<HealthStatus>('/api/health');
  },

  async getOverview(
    decisionDate: string,
    cutoffTime: string,
    matchingMode: MatchingMode = 'exact'
  ): Promise<OverviewResponse> {
    const params = new URLSearchParams({
      decision_date: decisionDate,
      cutoff_time: cutoffTime,
      matching_mode: matchingMode,
    });
    return fetchJson<OverviewResponse>(`/api/analysis/overview?${params.toString()}`);
  },

  async getForecast(
    decisionDate: string,
    cutoffTime: string,
    matchingMode: MatchingMode = 'exact'
  ): Promise<ForecastExplorerResponse> {
    const params = new URLSearchParams({
      decision_date: decisionDate,
      cutoff_time: cutoffTime,
      matching_mode: matchingMode,
    });
    return fetchJson<ForecastExplorerResponse>(`/api/analysis/forecast?${params.toString()}`);
  },

  async getRecords(
    decisionDate: string,
    cutoffTime: string,
    matchingMode: MatchingMode = 'exact'
  ): Promise<RecordsResponse> {
    const params = new URLSearchParams({
      decision_date: decisionDate,
      cutoff_time: cutoffTime,
      matching_mode: matchingMode,
    });
    return fetchJson<RecordsResponse>(`/api/analysis/records?${params.toString()}`);
  },

  async getAccuracy(
    startDate: string,
    endDate: string,
    cutoffTime: string,
    matchingMode: MatchingMode = 'exact'
  ): Promise<AccuracyAnalysisResponse> {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      cutoff_time: cutoffTime,
      matching_mode: matchingMode,
    });
    return fetchJson<AccuracyAnalysisResponse>(`/api/analysis/accuracy?${params.toString()}`);
  },

  getExportUrl(
    decisionDate: string,
    cutoffTime: string,
    matchingMode: MatchingMode = 'exact'
  ): string {
    const params = new URLSearchParams({
      decision_date: decisionDate,
      cutoff_time: cutoffTime,
      matching_mode: matchingMode,
    });
    return `${API_BASE}/api/analysis/export?${params.toString()}`;
  },

  async downloadCsv(
    decisionDate: string,
    cutoffTime: string,
    matchingMode: MatchingMode = 'exact'
  ): Promise<void> {
    const url = this.getExportUrl(decisionDate, cutoffTime, matchingMode);
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Export failed with status ${res.status}`);
    }
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `windscope_${decisionDate}_${cutoffTime.replace(':', '')}_${matchingMode}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    a.remove();
  },
};
