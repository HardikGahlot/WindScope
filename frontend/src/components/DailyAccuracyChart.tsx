import React from 'react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { DailyTrendItem } from '../types';

interface DailyAccuracyChartProps {
  trends: DailyTrendItem[];
  selectedDate: string;
  onSelectDate: (date: string) => void;
}

export const DailyAccuracyChart: React.FC<DailyAccuracyChartProps> = ({
  trends,
  selectedDate,
  onSelectDate,
}) => {
  const chartData = trends.map((t) => {
    const dayLabel = t.decision_date.slice(8); // '01', '02', etc.
    return {
      date: t.decision_date,
      dayLabel: `Jan ${dayLabel}`,
      mae: t.mae,
      bias: t.bias,
      mape: t.mape,
      matched: t.matched_periods,
      avgActual: t.avg_actual_mw,
      avgForecast: t.avg_forecast_mw,
      isSelected: t.decision_date === selectedDate,
    };
  });

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-navy-900 border border-slate-700 rounded-lg p-3 shadow-xl text-xs space-y-1.5 min-w-[200px]">
          <div className="font-semibold text-white border-b border-slate-800 pb-1 flex justify-between">
            <span>Decision: {data.date}</span>
            <span className="text-brand-cyan">Day-Ahead</span>
          </div>
          <div className="space-y-1 pt-0.5">
            <div className="flex justify-between text-slate-300">
              <span className="text-amber-400">MAE:</span>
              <span className="font-mono font-bold">
                {data.mae !== null ? `${data.mae.toLocaleString()} MW` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Mean Bias:</span>
              <span
                className={`font-mono font-bold ${
                  (data.bias || 0) > 0
                    ? 'text-amber-400'
                    : (data.bias || 0) < 0
                    ? 'text-cyan-400'
                    : 'text-slate-200'
                }`}
              >
                {data.bias !== null
                  ? `${data.bias > 0 ? '+' : ''}${data.bias.toLocaleString()} MW`
                  : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>MAPE:</span>
              <span className="font-mono font-bold">
                {data.mape !== null ? `${data.mape.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800">
              Matched: {data.matched} half-hour periods
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-navy-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-white tracking-wide">
            January 2026 Daily Forecast Accuracy &amp; Bias Trends
          </h2>
          <p className="text-xs text-slate-400">
            Click any bar/point to inspect that specific decision date. Bars indicate MAE; line indicates Mean Bias.
          </p>
        </div>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 bg-amber-500/30 border border-amber-400 inline-block rounded-sm"></span>
            <span className="text-slate-300">Daily MAE (MW)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-cyan-400 inline-block"></span>
            <span className="text-slate-300">Mean Bias (MW)</span>
          </div>
        </div>
      </div>

      <div className="h-64 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
            onClick={(state) => {
              if (state && state.activePayload && state.activePayload.length) {
                const date = state.activePayload[0].payload.date;
                onSelectDate(date);
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="dayLabel"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              tick={{ fill: '#94a3b8' }}
              interval={1}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
              tick={{ fill: '#94a3b8' }}
            />
            <ReferenceLine y={0} stroke="#475569" strokeDasharray="2 2" />
            <Tooltip content={<CustomTooltip />} />

            {/* Daily MAE Bars */}
            <Bar
              dataKey="mae"
              name="MAE"
              fill="#f59e0b"
              opacity={0.4}
              radius={[3, 3, 0, 0]}
              cursor="pointer"
            />

            {/* Daily Bias Line */}
            <Line
              type="monotone"
              dataKey="bias"
              name="Mean Bias"
              stroke="#06b6d4"
              strokeWidth={2}
              dot={{ r: 2.5, fill: '#06b6d4' }}
              activeDot={{ r: 5, fill: '#22d3ee' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
