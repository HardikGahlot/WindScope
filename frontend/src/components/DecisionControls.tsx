import React, { useState } from 'react';
import { ArrowRight, Calendar, Clock, RefreshCw } from 'lucide-react';
import { MatchingMode } from '../types';

interface DecisionControlsProps {
  decisionDate: string;
  onDecisionDateChange: (date: string) => void;
  cutoffTime: string;
  onCutoffTimeChange: (time: string) => void;
  matchingMode: MatchingMode;
  onMatchingModeChange: (mode: MatchingMode) => void;
  isLoading: boolean;
  onRefresh: () => void;
}

export const DecisionControls: React.FC<DecisionControlsProps> = ({
  decisionDate,
  onDecisionDateChange,
  cutoffTime,
  onCutoffTimeChange,
  matchingMode,
  onMatchingModeChange,
  isLoading,
  onRefresh,
}) => {
  const [localCutoff, setLocalCutoff] = useState(cutoffTime);
  const [cutoffError, setCutoffError] = useState<string | null>(null);

  // Compute delivery date (following day)
  const deliveryDateObj = new Date(decisionDate);
  deliveryDateObj.setDate(deliveryDateObj.getDate() + 1);
  const deliveryDateStr = deliveryDateObj.toISOString().split('T')[0];

  const handleCutoffSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parts = localCutoff.trim().split(':');
    if (parts.length !== 2) {
      setCutoffError('Format must be HH:MM');
      return;
    }
    const h = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    if (isNaN(h) || isNaN(m) || h < 0 || h > 23 || m < 0 || m > 59) {
      setCutoffError('Hour 00-23, Minute 00-59');
      return;
    }
    setCutoffError(null);
    const formatted = `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
    setLocalCutoff(formatted);
    onCutoffTimeChange(formatted);
  };

  const setPresetCutoff = (preset: string) => {
    setLocalCutoff(preset);
    setCutoffError(null);
    onCutoffTimeChange(preset);
  };

  return (
    <div className="bg-navy-900 border border-slate-800 rounded-xl p-4 sm:p-5 shadow-sm space-y-4">
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        {/* Date Context: Decision Date -> Delivery Date */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Decision Date selector */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1">
              <Calendar className="w-3 h-3 text-brand-cyan" />
              Decision Date (Wholesale Purchasing)
            </label>
            <div className="relative">
              <input
                type="date"
                min="2026-01-01"
                max="2026-01-31"
                value={decisionDate}
                onChange={(e) => onDecisionDateChange(e.target.value)}
                className="bg-navy-800 border border-slate-700 text-white text-xs font-mono rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-cyan focus:border-brand-cyan"
              />
            </div>
          </div>

          {/* Forward arrow */}
          <div className="hidden sm:flex items-center text-slate-500 pt-5">
            <ArrowRight className="w-4 h-4 text-brand-cyan" />
          </div>

          {/* Delivery Date Display */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">
              Delivery Date (Physical Infeed)
            </label>
            <div className="bg-navy-800/60 border border-slate-700/60 rounded-lg px-3 py-2 text-xs font-mono text-emerald-400 flex items-center gap-2">
              <span>{deliveryDateStr}</span>
              <span className="text-[10px] text-slate-400 uppercase font-sans font-medium px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                Day-Ahead
              </span>
            </div>
          </div>
        </div>

        {/* Cutoff Time Configuration */}
        <div className="flex flex-wrap items-end gap-3">
          <form onSubmit={handleCutoffSubmit} className="flex items-end gap-2">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-medium text-slate-400 flex items-center gap-1">
                  <Clock className="w-3 h-3 text-amber-400" />
                  Decision Cutoff (Europe/London)
                </label>
              </div>
              <div className="flex items-center space-x-1.5">
                <input
                  type="text"
                  maxLength={5}
                  value={localCutoff}
                  onChange={(e) => setLocalCutoff(e.target.value)}
                  placeholder="09:30"
                  className="w-20 bg-navy-800 border border-slate-700 text-white text-xs font-mono text-center rounded-lg py-2 focus:outline-none focus:ring-1 focus:ring-amber-400 focus:border-amber-400"
                />
                <button
                  type="submit"
                  disabled={localCutoff === cutoffTime}
                  className="px-2.5 py-2 text-xs font-medium rounded-lg bg-navy-700 hover:bg-navy-600 disabled:opacity-40 disabled:hover:bg-navy-700 text-slate-200 border border-slate-600 transition-colors"
                >
                  Apply
                </button>
              </div>
              {cutoffError && (
                <p className="text-[10px] text-rose-400 mt-0.5">{cutoffError}</p>
              )}
            </div>
          </form>

          {/* Quick Presets */}
          <div className="flex items-center space-x-1 pb-0.5">
            <button
              onClick={() => setPresetCutoff('09:30')}
              className={`px-2 py-1 text-[11px] font-mono rounded border transition-colors ${
                cutoffTime === '09:30'
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-navy-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
              title="Default MVP demonstration cutoff"
            >
              09:30 (MVP)
            </button>
            <button
              onClick={() => setPresetCutoff('11:00')}
              className={`px-2 py-1 text-[11px] font-mono rounded border transition-colors ${
                cutoffTime === '11:00'
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-navy-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
              title="UK Day-Ahead Auction Deadline"
            >
              11:00
            </button>
            <button
              onClick={() => setPresetCutoff('12:00')}
              className={`px-2 py-1 text-[11px] font-mono rounded border transition-colors ${
                cutoffTime === '12:00'
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-navy-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
              title="Midday Gate Closure"
            >
              12:00
            </button>
          </div>

          {/* Resolution Matching Toggle */}
          <div className="flex items-center bg-navy-800 p-1 rounded-lg border border-slate-700">
            <button
              onClick={() => onMatchingModeChange('exact')}
              className={`px-2.5 py-1 text-xs rounded-md transition-all font-medium ${
                matchingMode === 'exact'
                  ? 'bg-navy-700 text-brand-cyan shadow-sm border border-slate-600'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Exact half-hour timestamp matching (24 matched :00, 24 missing :30)"
            >
              Exact Resolution
            </button>
            <button
              onClick={() => onMatchingModeChange('mapped_hourly')}
              className={`px-2.5 py-1 text-xs rounded-md transition-all font-medium ${
                matchingMode === 'mapped_hourly'
                  ? 'bg-navy-700 text-brand-cyan shadow-sm border border-slate-600'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Map hourly WINDFOR forecasts to both half-hourly settlement periods"
            >
              Mapped Block Hour
            </button>
          </div>

          {/* Refresh button */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="p-2 text-slate-300 hover:text-white bg-navy-800 hover:bg-navy-700 border border-slate-700 rounded-lg transition-colors disabled:opacity-50"
            title="Refresh analysis"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-brand-cyan' : ''}`} />
          </button>
        </div>
      </div>

      {/* Explanatory banner */}
      <div className="text-[11px] text-slate-400 bg-navy-950/60 border border-slate-800/80 rounded-lg px-3 py-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1">
        <div>
          <span className="text-brand-cyan font-medium">Domain Rule:</span> Only forecasts published on or before{' '}
          <span className="font-mono text-slate-200">{cutoffTime} Europe/London</span> on the decision date are eligible. All later updates are strictly excluded to replicate real day-ahead decision conditions.
        </div>
        <div className="text-slate-500 text-[10px]">
          Demo Cutoff: 09:30 UK Time (Configurable)
        </div>
      </div>
    </div>
  );
};
