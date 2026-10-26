import React from 'react';
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart2,
  CheckCircle2,
  Layers,
  Zap,
} from 'lucide-react';
import { OverviewResponse } from '../types';

interface ExecutiveOverviewProps {
  overview: OverviewResponse;
}

export const ExecutiveOverview: React.FC<ExecutiveOverviewProps> = ({ overview }) => {
  const { metrics } = overview;
  const isBiasOver = (metrics.bias ?? 0) > 0;
  const isBiasUnder = (metrics.bias ?? 0) < 0;

  return (
    <div className="space-y-4">
      {/* Top Provenance Ribbon */}
      <div className="bg-navy-900 border border-slate-800 rounded-xl px-4 py-3 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-1">
          <div>
            <span className="text-slate-400">Decision Date:</span>{' '}
            <span className="font-mono text-white font-medium">{overview.decision_date}</span>
          </div>
          <div>
            <span className="text-slate-400">Delivery Date:</span>{' '}
            <span className="font-mono text-emerald-400 font-medium">{overview.delivery_date}</span>
          </div>
          <div>
            <span className="text-slate-400">Configured Cutoff:</span>{' '}
            <span className="font-mono text-amber-300 font-medium">{overview.decision_cutoff_london}</span>
          </div>
          <div>
            <span className="text-slate-400">Latest Eligible Publication:</span>{' '}
            <span className="font-mono text-brand-cyan font-medium">
              {overview.latest_eligible_publish_time_london || 'None available before cutoff'}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium border ${
            overview.matching_mode === 'exact'
              ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
              : 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
          }`}>
            {overview.matching_mode === 'exact' ? 'Exact Resolution (24 Matched / 24 Gap)' : 'Mapped Block Hour (48 Matched)'}
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            {overview.data_source}
          </span>
        </div>
      </div>

      {/* Main KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Expected vs Actual Generation */}
        <div className="bg-navy-900 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Wind Generation (Avg)</span>
            <Zap className="w-4 h-4 text-brand-cyan" />
          </div>
          <div className="space-y-1">
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-slate-400">Decision Forecast:</span>
              <span className="text-lg font-bold font-mono text-brand-cyan">
                {overview.expected_wind_generation_avg_mw !== null
                  ? `${overview.expected_wind_generation_avg_mw.toLocaleString()} MW`
                  : 'N/A'}
              </span>
            </div>
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-slate-400">Actual Outturn:</span>
              <span className="text-lg font-bold font-mono text-emerald-400">
                {overview.actual_wind_generation_avg_mw !== null
                  ? `${overview.actual_wind_generation_avg_mw.toLocaleString()} MW`
                  : 'N/A'}
              </span>
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex justify-between text-[11px] text-slate-400">
            <span>Peak Expected: {overview.expected_wind_generation_peak_mw?.toLocaleString() ?? '—'} MW</span>
            <span>Peak Actual: {overview.actual_wind_generation_peak_mw?.toLocaleString() ?? '—'} MW</span>
          </div>
        </div>

        {/* Card 2: Mean Absolute Error (MAE) */}
        <div className="bg-navy-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Mean Absolute Error</span>
            <BarChart2 className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">
              {metrics.mae !== null ? metrics.mae.toLocaleString() : 'N/A'}
            </span>
            <span className="text-xs text-slate-400 font-mono">MW</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Average magnitude of error per matched half-hour delivery period.
          </p>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-400 flex justify-between">
            <span>RMSE: {metrics.rmse !== null ? `${metrics.rmse.toLocaleString()} MW` : 'N/A'}</span>
            <span>Max Abs: {metrics.max_absolute_error_mw?.toLocaleString() ?? '—'} MW</span>
          </div>
        </div>

        {/* Card 3: Forecast Bias */}
        <div className="bg-navy-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Mean Forecast Bias</span>
            {isBiasOver ? (
              <ArrowUpRight className="w-4 h-4 text-amber-400" />
            ) : isBiasUnder ? (
              <ArrowDownRight className="w-4 h-4 text-brand-cyan" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            )}
          </div>
          <div className="flex items-baseline gap-2">
            <span
              className={`text-2xl font-bold font-mono ${
                isBiasOver ? 'text-amber-400' : isBiasUnder ? 'text-cyan-400' : 'text-slate-100'
              }`}
            >
              {metrics.bias !== null
                ? `${metrics.bias > 0 ? '+' : ''}${metrics.bias.toLocaleString()}`
                : 'N/A'}
            </span>
            <span className="text-xs text-slate-400 font-mono">MW</span>
          </div>
          <div className="text-[11px] font-medium mt-1">
            {isBiasOver && (
              <span className="text-amber-400/90">Overforecast bias (Forecasted &gt; Actual)</span>
            )}
            {isBiasUnder && (
              <span className="text-cyan-400/90">Underforecast bias (Forecasted &lt; Actual)</span>
            )}
            {!isBiasOver && !isBiasUnder && (
              <span className="text-slate-400">Zero net bias across matched periods</span>
            )}
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-400 flex justify-between">
            <span>Over: {metrics.overforecast_count} periods</span>
            <span>Under: {metrics.underforecast_count} periods</span>
          </div>
        </div>

        {/* Card 4: Observational Coverage & MAPE */}
        <div className="bg-navy-900 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Coverage &amp; MAPE</span>
            <Layers className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline justify-between">
            <div>
              <div className="text-2xl font-bold font-mono text-white">
                {metrics.coverage_percentage}%
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                {metrics.matched_periods_count} of {metrics.total_expected_periods} matched periods
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs text-slate-400 block">MAPE</span>
              <span className="text-base font-bold font-mono text-emerald-400">
                {metrics.mape !== null ? `${metrics.mape.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-400 flex justify-between">
            <span>Missing: {metrics.missing_forecast_count} fcst / {metrics.missing_actual_count} act</span>
            {metrics.mape_excluded_zero_actuals_count > 0 && (
              <span title="Periods where Actual = 0 MW excluded to avoid division by zero">
                {metrics.mape_excluded_zero_actuals_count} zero-act excluded
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
