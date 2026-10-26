import React, { useCallback, useEffect, useState } from 'react';
import {
  BarChart3,
  LineChart,
  Table,
} from 'lucide-react';
import { DailyAccuracyChart } from './components/DailyAccuracyChart';
import { DecisionControls } from './components/DecisionControls';
import { ErrorMessage } from './components/ErrorMessage';
import { ExecutiveOverview } from './components/ExecutiveOverview';
import { ForecastActualChart } from './components/ForecastActualChart';
import { LoadingSkeleton } from './components/LoadingSkeleton';
import { MethodologyPanel } from './components/MethodologyPanel';
import { RecordsTable } from './components/RecordsTable';
import { TopBar } from './components/TopBar';
import { api } from './services/api';
import {
  AccuracyAnalysisResponse,
  MatchedDeliveryRecord,
  MatchingMode,
  OverviewResponse,
} from './types';

export const App: React.FC = () => {
  const [decisionDate, setDecisionDate] = useState('2026-01-10');
  const [cutoffTime, setCutoffTime] = useState('09:30');
  const [matchingMode, setMatchingMode] = useState<MatchingMode>('exact');

  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [records, setRecords] = useState<MatchedDeliveryRecord[]>([]);
  const [accuracy, setAccuracy] = useState<AccuracyAnalysisResponse | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloadingCsv, setIsDownloadingCsv] = useState(false);
  const [isMethodologyOpen, setIsMethodologyOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'daily' | 'trends' | 'table'>('daily');

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Parallel requests for daily overview, delivery records, and monthly trends
      const [overviewData, recordsData, accuracyData] = await Promise.all([
        api.getOverview(decisionDate, cutoffTime, matchingMode),
        api.getRecords(decisionDate, cutoffTime, matchingMode),
        api.getAccuracy('2026-01-01', '2026-01-31', cutoffTime, matchingMode),
      ]);

      setOverview(overviewData);
      setRecords(recordsData.records);
      setAccuracy(accuracyData);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch data from WindScope API.');
    } finally {
      setIsLoading(false);
    }
  }, [decisionDate, cutoffTime, matchingMode]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleDownloadCsv = async () => {
    try {
      setIsDownloadingCsv(true);
      await api.downloadCsv(decisionDate, cutoffTime, matchingMode);
    } catch (err: any) {
      alert(`CSV Export failed: ${err.message}`);
    } finally {
      setIsDownloadingCsv(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy-950 flex flex-col">
      {/* Top Navigation */}
      <TopBar
        onOpenMethodology={() => setIsMethodologyOpen(true)}
        upstreamStatus={overview?.retrieval_status}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6 space-y-6">
        {/* Decision & Filter Controls */}
        <DecisionControls
          decisionDate={decisionDate}
          onDecisionDateChange={setDecisionDate}
          cutoffTime={cutoffTime}
          onCutoffTimeChange={setCutoffTime}
          matchingMode={matchingMode}
          onMatchingModeChange={setMatchingMode}
          isLoading={isLoading}
          onRefresh={loadData}
        />

        {/* Error Notification */}
        {error && <ErrorMessage message={error} onRetry={loadData} />}

        {/* Loading State */}
        {isLoading && !overview && <LoadingSkeleton />}

        {/* Main Content Area */}
        {overview && (
          <div className="space-y-6">
            {/* Section A: Executive Overview */}
            <ExecutiveOverview overview={overview} />

            {/* Navigation Tabs */}
            <div className="flex border-b border-slate-800 space-x-6 text-xs font-medium">
              <button
                onClick={() => setActiveTab('daily')}
                className={`pb-3 flex items-center gap-1.5 transition-colors border-b-2 ${
                  activeTab === 'daily'
                    ? 'border-brand-cyan text-brand-cyan'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <LineChart className="w-4 h-4" />
                <span>Forecast vs Actual Delivery Profile</span>
              </button>
              <button
                onClick={() => setActiveTab('trends')}
                className={`pb-3 flex items-center gap-1.5 transition-colors border-b-2 ${
                  activeTab === 'trends'
                    ? 'border-brand-cyan text-brand-cyan'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>January 2026 Accuracy Trends</span>
              </button>
              <button
                onClick={() => setActiveTab('table')}
                className={`pb-3 flex items-center gap-1.5 transition-colors border-b-2 ${
                  activeTab === 'table'
                    ? 'border-brand-cyan text-brand-cyan'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Table className="w-4 h-4" />
                <span>Audit Records Table ({records.length})</span>
              </button>
            </div>

            {/* Tab 1: Daily Delivery Chart & Records */}
            {activeTab === 'daily' && (
              <div className="space-y-6">
                <ForecastActualChart
                  records={records}
                  deliveryDate={overview.delivery_date}
                  cutoffTime={cutoffTime}
                />
                <RecordsTable
                  records={records}
                  onDownloadCsv={handleDownloadCsv}
                  isDownloadingCsv={isDownloadingCsv}
                />
              </div>
            )}

            {/* Tab 2: Monthly Trends */}
            {activeTab === 'trends' && accuracy && (
              <div className="space-y-6">
                <DailyAccuracyChart
                  trends={accuracy.daily_trends}
                  selectedDate={decisionDate}
                  onSelectDate={(newDate) => {
                    setDecisionDate(newDate);
                    setActiveTab('daily');
                  }}
                />

                {/* Aggregate Summary Box */}
                <div className="bg-navy-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3 text-xs">
                  <h3 className="font-semibold text-white">
                    January 2026 Aggregate Performance (31 Decision Days)
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-1 font-mono">
                    <div>
                      <span className="text-slate-400 text-[11px] block">Overall MAE:</span>
                      <span className="text-base font-bold text-amber-400">
                        {accuracy.aggregate_metrics.mae?.toLocaleString()} MW
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[11px] block">Overall RMSE:</span>
                      <span className="text-base font-bold text-slate-100">
                        {accuracy.aggregate_metrics.rmse?.toLocaleString()} MW
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[11px] block">Overall Mean Bias:</span>
                      <span
                        className={`text-base font-bold ${
                          (accuracy.aggregate_metrics.bias ?? 0) > 0
                            ? 'text-amber-400'
                            : 'text-cyan-400'
                        }`}
                      >
                        {(accuracy.aggregate_metrics.bias ?? 0) > 0 ? '+' : ''}
                        {accuracy.aggregate_metrics.bias?.toLocaleString()} MW
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[11px] block">Total Matched Pairs:</span>
                      <span className="text-base font-bold text-emerald-400">
                        {accuracy.aggregate_metrics.matched_periods_count.toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: Detailed Records Table */}
            {activeTab === 'table' && (
              <RecordsTable
                records={records}
                onDownloadCsv={handleDownloadCsv}
                isDownloadingCsv={isDownloadingCsv}
              />
            )}
          </div>
        )}
      </main>

      {/* Methodology Modal */}
      <MethodologyPanel
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-navy-900/60 px-4 py-4 mt-auto text-center text-xs text-slate-500">
        <p>
          WindScope — UK Wind Forecast Intelligence &bull; Built with FastAPI &amp; React &bull; Powered by Elexon BMRS Open Data
        </p>
      </footer>
    </div>
  );
};

export default App;
