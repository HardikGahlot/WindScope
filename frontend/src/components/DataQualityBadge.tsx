import React from 'react';

interface DataQualityBadgeProps {
  flag: string;
}

export const DataQualityBadge: React.FC<DataQualityBadgeProps> = ({ flag }) => {
  switch (flag) {
    case 'HOURLY_RESOLUTION_NO_EXACT_HALF_HOUR_FORECAST':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
          Hourly WINDFOR (:30 gap)
        </span>
      );
    case 'MAPPED_FROM_HOURLY_FORECAST':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
          Mapped from :00 Hour
        </span>
      );
    case 'ALL_CANDIDATES_PUBLISHED_AFTER_CUTOFF':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          Published After Cutoff
        </span>
      );
    case 'ZERO_ACTUAL_EXCLUDED_FROM_MAPE':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
          Actual = 0 (No MAPE)
        </span>
      );
    case 'DUPLICATE_PUBLICATION_RESOLVED':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
          Deduped
        </span>
      );
    case 'ACTUAL_DATA_MISSING':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
          Actual Missing
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
          {flag}
        </span>
      );
  }
};
