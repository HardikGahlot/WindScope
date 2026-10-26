import React from 'react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Overview skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 bg-navy-900/60 rounded-xl border border-slate-800"></div>
        ))}
      </div>

      {/* Chart skeleton */}
      <div className="h-80 bg-navy-900/60 rounded-xl border border-slate-800"></div>

      {/* Table skeleton */}
      <div className="h-64 bg-navy-900/60 rounded-xl border border-slate-800"></div>
    </div>
  );
};
