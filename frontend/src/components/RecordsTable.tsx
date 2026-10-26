import React, { useMemo, useState } from 'react';
import {
  ArrowUpDown,
  Download,
  Filter,
  Search,
} from 'lucide-react';
import { MatchedDeliveryRecord } from '../types';
import { DataQualityBadge } from './DataQualityBadge';

interface RecordsTableProps {
  records: MatchedDeliveryRecord[];
  onDownloadCsv: () => void;
  isDownloadingCsv: boolean;
}

type SortField =
  | 'settlement_period'
  | 'delivery_time_london'
  | 'forecast_generation_mw'
  | 'actual_generation_mw'
  | 'error_mw'
  | 'abs_error_mw'
  | 'percentage_error'
  | 'publish_time_london';

export const RecordsTable: React.FC<RecordsTableProps> = ({
  records,
  onDownloadCsv,
  isDownloadingCsv,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('settlement_period');
  const [sortAsc, setSortAsc] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 12;

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const filteredAndSortedRecords = useMemo(() => {
    return records
      .filter((r) => {
        // Status filter
        if (statusFilter !== 'all' && r.match_status !== statusFilter) {
          return false;
        }
        // Search filter
        if (searchTerm) {
          const term = searchTerm.toLowerCase();
          const matchPeriod = r.settlement_period.toString().includes(term);
          const matchTime = r.delivery_time_london.toLowerCase().includes(term);
          const matchFlags = r.data_quality_flags.some((f) => f.toLowerCase().includes(term));
          return matchPeriod || matchTime || matchFlags;
        }
        return true;
      })
      .sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];

        if (valA === null || valA === undefined) return sortAsc ? 1 : -1;
        if (valB === null || valB === undefined) return sortAsc ? -1 : 1;

        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortAsc ? valA - valB : valB - valA;
        }
        return sortAsc
          ? String(valA).localeCompare(String(valB))
          : String(valB).localeCompare(String(valA));
      });
  }, [records, searchTerm, statusFilter, sortField, sortAsc]);

  const totalPages = Math.ceil(filteredAndSortedRecords.length / pageSize) || 1;
  const paginatedRecords = filteredAndSortedRecords.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div className="bg-navy-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-white tracking-wide">
            Settlement Period Records &amp; Quality Audit
          </h2>
          <p className="text-xs text-slate-400">
            Audit half-hourly forecasts, publication provenance, actual generation, and errors.
          </p>
        </div>

        {/* Action button: CSV Export */}
        <button
          onClick={onDownloadCsv}
          disabled={isDownloadingCsv}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-medium transition-colors shadow-sm"
        >
          <Download className="w-3.5 h-3.5" />
          <span>{isDownloadingCsv ? 'Exporting...' : 'Export CSV (Audit)'}</span>
        </button>
      </div>

      {/* Filter and search bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 text-xs">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by period, time, flag..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full pl-9 pr-3 py-1.5 bg-navy-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-brand-cyan"
          />
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-navy-800 border border-slate-700 text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-brand-cyan text-xs"
          >
            <option value="all">All Match Statuses ({records.length})</option>
            <option value="matched">Matched Only</option>
            <option value="missing_forecast">Missing Forecast</option>
            <option value="missing_actual">Missing Actual</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-slate-800 rounded-lg">
        <table className="w-full text-left text-xs">
          <thead className="bg-navy-800/80 text-slate-300 font-medium border-b border-slate-800">
            <tr>
              <th
                onClick={() => handleSort('settlement_period')}
                className="py-2.5 px-3 cursor-pointer hover:text-white"
              >
                <div className="flex items-center gap-1">
                  <span>Period</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                onClick={() => handleSort('delivery_time_london')}
                className="py-2.5 px-3 cursor-pointer hover:text-white"
              >
                <div className="flex items-center gap-1">
                  <span>Delivery Time (London)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                onClick={() => handleSort('forecast_generation_mw')}
                className="py-2.5 px-3 text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  <span>Forecast (MW)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                onClick={() => handleSort('actual_generation_mw')}
                className="py-2.5 px-3 text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  <span>Actual (MW)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                onClick={() => handleSort('error_mw')}
                className="py-2.5 px-3 text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  <span>Error (F - A)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                onClick={() => handleSort('percentage_error')}
                className="py-2.5 px-3 text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  <span>APE (%)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                onClick={() => handleSort('publish_time_london')}
                className="py-2.5 px-3 cursor-pointer hover:text-white"
              >
                <div className="flex items-center gap-1">
                  <span>Published At</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th className="py-2.5 px-3">Quality &amp; Provenance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {paginatedRecords.length > 0 ? (
              paginatedRecords.map((r) => {
                const isOver = (r.error_mw ?? 0) > 0;
                const isUnder = (r.error_mw ?? 0) < 0;

                return (
                  <tr key={r.settlement_period} className="hover:bg-navy-800/40 transition-colors">
                    <td className="py-2.5 px-3 text-slate-300 font-semibold">
                      SP {r.settlement_period}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">
                      <div>{r.delivery_time_london}</div>
                      <div className="text-[10px] text-slate-500 font-sans">
                        {r.delivery_time_utc.slice(11, 16)} UTC
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-right text-cyan-300">
                      {r.forecast_generation_mw !== null
                        ? r.forecast_generation_mw.toLocaleString()
                        : <span className="text-slate-600 font-sans italic">—</span>}
                    </td>
                    <td className="py-2.5 px-3 text-right text-emerald-400">
                      {r.actual_generation_mw !== null
                        ? r.actual_generation_mw.toLocaleString()
                        : <span className="text-slate-600 font-sans italic">—</span>}
                    </td>
                    <td
                      className={`py-2.5 px-3 text-right font-bold ${
                        isOver
                          ? 'text-amber-400'
                          : isUnder
                          ? 'text-cyan-400'
                          : 'text-slate-400'
                      }`}
                    >
                      {r.error_mw !== null ? (
                        `${r.error_mw > 0 ? '+' : ''}${r.error_mw.toLocaleString()}`
                      ) : (
                        <span className="text-slate-600 font-sans font-normal italic">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-300">
                      {r.percentage_error !== null
                        ? `${r.percentage_error.toFixed(1)}%`
                        : <span className="text-slate-600 font-sans italic">—</span>}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                      {r.publish_time_london || <span className="text-slate-600 italic">—</span>}
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      <div className="flex flex-wrap gap-1">
                        {r.data_quality_flags.map((flag, idx) => (
                          <DataQualityBadge key={idx} flag={flag} />
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-500 font-sans">
                  No records match the current search or status filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
        <div>
          Showing {paginatedRecords.length} of {filteredAndSortedRecords.length} settlement periods
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-2.5 py-1 rounded bg-navy-800 border border-slate-700 disabled:opacity-40 hover:bg-navy-700 text-slate-200"
          >
            Previous
          </button>
          <span className="px-2">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-2.5 py-1 rounded bg-navy-800 border border-slate-700 disabled:opacity-40 hover:bg-navy-700 text-slate-200"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
