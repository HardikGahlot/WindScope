import React from 'react';
import { AlertCircle, BookOpen, X } from 'lucide-react';

interface MethodologyPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MethodologyPanel: React.FC<MethodologyPanelProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="bg-navy-900 border border-slate-700/80 rounded-2xl max-w-3xl w-full max-h-[85vh] overflow-y-auto shadow-2xl p-6 text-slate-200 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-2.5">
            <BookOpen className="w-5 h-5 text-brand-cyan" />
            <h2 className="text-base font-bold text-white">
              WindScope Methodology, Time Semantics &amp; Data Provenance
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-navy-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Section 1: Data Sources */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-brand-cyan">
            1. Official Elexon BMRS Datasets
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            All data is retrieved from Elexon BMRS (Balancing Mechanism Reporting Service) APIs:
          </p>
          <ul className="text-xs space-y-1.5 list-disc list-inside text-slate-300">
            <li>
              <span className="font-mono text-cyan-300">FUELHH/stream</span>: Actual national generation by fuel type at 30-minute intervals. Filtered strictly for{' '}
              <span className="font-mono text-emerald-400">fuelType = 'WIND'</span>.
            </li>
            <li>
              <span className="font-mono text-cyan-300">WINDFOR/stream</span>: Wind generation forecast stream issued by National Grid ESO (NGESO). Contains historical publication runs.
            </li>
          </ul>
        </div>

        {/* Section 2: Time Semantics & Decision Cutoff */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-brand-cyan">
            2. Decision Cutoff &amp; Historical Selection Algorithm
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            In wholesale electricity procurement, day-ahead purchase decisions for delivery on Day{' '}
            <span className="font-mono text-white">D+1</span> must be finalized on Day{' '}
            <span className="font-mono text-white">D</span> before a specific operational deadline (e.g., 09:30 Europe/London).
          </p>
          <div className="bg-navy-950 border border-slate-800 rounded-lg p-3 text-xs space-y-2 font-mono">
            <div className="text-slate-400">// Retrospective Forecast Selection Rule</div>
            <div>
              1. Determine cutoff in UTC: <span className="text-amber-300">cutoff_utc = decision_date @ cutoff_time (Europe/London)</span>
            </div>
            <div>
              2. Filter WINDFOR records targeting delivery period: <span className="text-emerald-400">startTime == delivery_period</span>
            </div>
            <div>
              3. Exclude future publications: <span className="text-rose-400">publishTime &gt; cutoff_utc</span>
            </div>
            <div>
              4. Select latest eligible: <span className="text-brand-cyan">max(publishTime) WHERE publishTime &le; cutoff_utc</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 italic">
            * 09:30 Europe/London is an MVP operational assumption for day-ahead decisions rather than a universal UK auction deadline. The interface allows users to adjust this cutoff dynamically.
          </p>
        </div>

        {/* Section 3: Hourly vs Half-Hourly Resolution */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-brand-cyan">
            3. Resolution Matching (Hourly Forecast vs Half-Hour Settlement)
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            In the UK market, settlement periods are half-hourly (48 settlement periods/day), whereas NGESO publishes WINDFOR forecasts at hourly resolution (<span className="font-mono text-white">:00</span>).
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="bg-navy-950 p-3 rounded-lg border border-slate-800">
              <span className="font-semibold text-white block mb-1">Exact Resolution Mode</span>
              <p className="text-slate-400">
                Matches only periods with exact <span className="font-mono">:00</span> timestamps. The <span className="font-mono">:30</span> settlement periods are presented with transparent gaps and flagged as missing forecast data.
              </p>
            </div>
            <div className="bg-navy-950 p-3 rounded-lg border border-slate-800">
              <span className="font-semibold text-white block mb-1">Mapped Block Hour Mode</span>
              <p className="text-slate-400">
                Maps the hourly forecast to both half-hour settlement periods in that block hour, providing complete 48-period evaluation while flagging each mapped observation.
              </p>
            </div>
          </div>
        </div>

        {/* Section 4: Accuracy Metrics */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-brand-cyan">
            4. Statistically Correct Accuracy Formulas
          </h3>
          <p className="text-xs text-slate-300">
            Let <span className="font-mono text-cyan-300">F</span> = forecast generation (MW),{' '}
            <span className="font-mono text-emerald-400">A</span> = actual generation (MW), and{' '}
            <span className="font-mono text-white">e = F - A</span> across{' '}
            <span className="font-mono text-white">N</span> valid matched pairs:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
            <div className="bg-navy-950 p-3 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans text-[11px]">Mean Absolute Error (MAE)</div>
              <div className="text-amber-300 text-sm mt-1">MAE = (1/N) &sum; |F - A|</div>
            </div>
            <div className="bg-navy-950 p-3 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans text-[11px]">Root Mean Squared Error (RMSE)</div>
              <div className="text-amber-300 text-sm mt-1">RMSE = &radic;((1/N) &sum; (F - A)&sup2;)</div>
            </div>
            <div className="bg-navy-950 p-3 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans text-[11px]">Mean Forecast Bias</div>
              <div className="text-cyan-300 text-sm mt-1">Bias = (1/N) &sum; (F - A)</div>
              <div className="text-[10px] text-slate-500 font-sans mt-0.5">
                + = Overforecast | - = Underforecast
              </div>
            </div>
            <div className="bg-navy-950 p-3 rounded-lg border border-slate-800">
              <div className="text-slate-400 font-sans text-[11px]">Mean Absolute Percentage Error (MAPE)</div>
              <div className="text-emerald-300 text-sm mt-1">MAPE = (1/M) &sum; |(F - A)/A| &times; 100</div>
              <div className="text-[10px] text-slate-500 font-sans mt-0.5">
                Strictly excludes A = 0 MW to avoid division by zero.
              </div>
            </div>
          </div>
        </div>

        {/* Section 5: Scope & Limitations */}
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3.5 text-xs text-amber-200/90 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-amber-300 block">Energy Market Domain Context &amp; Disclaimers</span>
            <p>
              1. Wind forecast error alone does not determine the total volume of electricity a utility must purchase; consumer demand, solar output, interconnector flows, and plant outages are outside this platform's national wind scope.
            </p>
            <p>
              2. WindScope is an independent analytical tool built for technical assessment and does not constitute trading execution software or an official Elexon service.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            Close Methodology
          </button>
        </div>
      </div>
    </div>
  );
};
