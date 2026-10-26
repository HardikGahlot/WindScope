import React from 'react';
import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { MatchedDeliveryRecord } from '../types';

interface ForecastActualChartProps {
  records: MatchedDeliveryRecord[];
  deliveryDate: string;
  cutoffTime: string;
  matchingMode?: 'exact' | 'mapped_hourly';
}

export const ForecastActualChart: React.FC<ForecastActualChartProps> = ({
  records,
  deliveryDate,
  cutoffTime,
  matchingMode = 'exact',
}) => {
  // Format data for Recharts
  const chartData = records.map((r) => {
    // Extract local time HH:MM from London representation
    const timeMatch = r.delivery_time_london.match(/(\d{2}:\d{2})/);
    const timeLabel = timeMatch ? timeMatch[1] : `SP ${r.settlement_period}`;

    return {
      period: r.settlement_period,
      timeLabel,
      fullTimeLondon: r.delivery_time_london,
      fullTimeUtc: r.delivery_time_utc,
      forecast: r.forecast_generation_mw,
      actual: r.actual_generation_mw,
      error: r.error_mw,
      publishTime: r.publish_time_london,
      status: r.match_status,
    };
  });

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-navy-900 border border-slate-700/80 rounded-lg p-3 shadow-xl text-xs space-y-1.5 min-w-[220px]">
          <div className="font-semibold text-white border-b border-slate-800 pb-1 flex justify-between">
            <span>Settlement Period {data.period}</span>
            <span className="font-mono text-brand-cyan">{data.timeLabel} London</span>
          </div>
          <div className="space-y-1 pt-0.5">
            <div className="flex justify-between items-center text-slate-300">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block"></span>
                Decision Forecast:
              </span>
              <span className="font-mono font-bold text-cyan-300">
                {data.forecast !== null ? `${data.forecast.toLocaleString()} MW` : 'Missing / Gap'}
              </span>
            </div>
            <div className="flex justify-between items-center text-slate-300">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block"></span>
                Actual Outturn:
              </span>
              <span className="font-mono font-bold text-emerald-300">
                {data.actual !== null ? `${data.actual.toLocaleString()} MW` : 'Missing'}
              </span>
            </div>
            {data.error !== null && (
              <div className="flex justify-between items-center text-slate-300 pt-1 border-t border-slate-800">
                <span>Forecast Error (F - A):</span>
                <span
                  className={`font-mono font-bold ${
                    data.error > 0 ? 'text-amber-400' : data.error < 0 ? 'text-cyan-400' : 'text-slate-200'
                  }`}
                >
                  {data.error > 0 ? `+${data.error.toLocaleString()}` : data.error.toLocaleString()} MW
                </span>
              </div>
            )}
            {data.publishTime && (
              <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800/80">
                Published: <span className="font-mono text-slate-300">{data.publishTime}</span>
              </div>
            )}
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
          <h2 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            Delivery Day Generation Profile: Decision Forecast vs Actual Outturn
          </h2>
          <p className="text-xs text-slate-400">
            Delivery Date: <span className="text-slate-200 font-mono">{deliveryDate}</span> (Cutoff:{' '}
            <span className="text-amber-300 font-mono">{cutoffTime} London</span>). Mode:{' '}
            <span className="text-brand-cyan font-mono font-medium">
              {matchingMode === 'exact' ? 'Exact Resolution (:30 gaps preserved)' : 'Mapped Block Hour (hourly spread)'}
            </span>.
          </p>
        </div>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-cyan-400 inline-block"></span>
            <span className="text-slate-300">Decision-Time Forecast (MW)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-emerald-400 inline-block"></span>
            <span className="text-slate-300">Actual Outturn (MW)</span>
          </div>
        </div>
      </div>

      <div className="h-80 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="timeLabel"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              interval={3}
              tick={{ fill: '#94a3b8' }}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
              tick={{ fill: '#94a3b8' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ display: 'none' }} />

            {/* Decision-Time Forecast line with GAPS for nulls */}
            <Line
              type="monotone"
              dataKey="forecast"
              name="Decision Forecast"
              stroke="#06b6d4"
              strokeWidth={2.5}
              dot={{ r: 2.5, fill: '#06b6d4', strokeWidth: 0 }}
              activeDot={{ r: 5, fill: '#22d3ee' }}
              connectNulls={false}
            />

            {/* Actual generation line */}
            <Line
              type="monotone"
              dataKey="actual"
              name="Actual Outturn"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ r: 2, fill: '#10b981', strokeWidth: 0 }}
              activeDot={{ r: 5, fill: '#34d399' }}
              connectNulls={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-800">
        <span>X-Axis: Half-hour delivery settlement periods (Europe/London)</span>
        <span>Y-Axis: National Wind Output (Megawatts)</span>
      </div>
    </div>
  );
};
