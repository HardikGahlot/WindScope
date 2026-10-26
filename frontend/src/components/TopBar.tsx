import React from 'react';
import { Activity, BookOpen, Clock, Wind } from 'lucide-react';

interface TopBarProps {
  onOpenMethodology: () => void;
  upstreamStatus?: string;
}

export const TopBar: React.FC<TopBarProps> = ({
  onOpenMethodology,
  upstreamStatus = 'connected',
}) => {
  return (
    <header className="border-b border-slate-800 bg-navy-900/90 backdrop-blur sticky top-0 z-30 px-4 lg:px-8 py-3.5">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        {/* Brand identity */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-cyan to-brand-emerald flex items-center justify-center shadow-lg shadow-cyan-500/10">
            <Wind className="w-5 h-5 text-navy-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                WindScope
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-brand-cyan/10 text-brand-cyan border border-brand-cyan/20">
                  GB Wholesale Day-Ahead
                </span>
              </h1>
            </div>
            <p className="text-xs text-slate-400">
              UK Wind Forecast Intelligence &amp; BMRS Outturn Accuracy Platform
            </p>
          </div>
        </div>

        {/* Right side operational telemetry */}
        <div className="flex items-center space-x-3 w-full sm:w-auto justify-between sm:justify-end text-xs">
          {/* Timezone badge */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-navy-800 border border-slate-700/60 text-slate-300">
            <Clock className="w-3.5 h-3.5 text-brand-cyan" />
            <span className="font-mono">Europe/London</span>
            <span className="text-slate-400 text-[10px]">(GMT / UTC+0)</span>
          </div>

          {/* Elexon source status */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-navy-800 border border-slate-700/60 text-slate-300">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span>Elexon BMRS:</span>
            <span className="font-medium text-emerald-400 capitalize">{upstreamStatus}</span>
          </div>

          {/* Methodology Trigger */}
          <button
            onClick={onOpenMethodology}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-navy-800 hover:bg-navy-700 text-slate-200 hover:text-white border border-slate-700 transition-colors shadow-sm"
            title="Inspect Data Methodology & Formulas"
          >
            <BookOpen className="w-3.5 h-3.5 text-brand-cyan" />
            <span className="font-medium">Methodology</span>
          </button>
        </div>
      </div>
    </header>
  );
};
