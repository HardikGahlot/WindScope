import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry }) => {
  return (
    <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-6 text-center space-y-3">
      <div className="w-10 h-10 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
        <AlertTriangle className="w-5 h-5" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-rose-300">Data Retrieval or Processing Error</h3>
        <p className="text-xs text-rose-200/80 mt-1 max-w-md mx-auto">{message}</p>
      </div>
      <div>
        <button
          onClick={onRetry}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5 text-brand-cyan" />
          <span>Retry Request</span>
        </button>
      </div>
    </div>
  );
};
