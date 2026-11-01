import React, { useState } from 'react';
import { Clock, PauseCircle, PlayCircle, Info, ChevronDown, ChevronUp } from 'lucide-react';

interface ClockDetails {
  total_seconds: number;
  total_hours: number;
  total_days: number;
  percentage?: number;
}

interface IntervalItem {
  id: number;
  stage_key: string;
  clock_type: string;
  start_time: string;
  end_time?: string;
  is_active: boolean;
  is_paused: boolean;
  elapsed_hours: number;
  elapsed_days: number;
  paused_seconds: number;
  rule_version: string;
}

interface ClockSummaryProps {
  clockData: {
    rule_version: string;
    institution_clock: ClockDetails;
    official_clock: ClockDetails;
    total_elapsed: ClockDetails;
    paused_duration?: ClockDetails;
    status: {
      is_active: boolean;
      is_paused: boolean;
      active_clock_type?: string;
    };
    explanation: string;
    interval_breakdown: IntervalItem[];
  };
  onPause?: (reason: string, clause?: string) => void;
  onResume?: () => void;
  canManageClock?: boolean;
}

export const DualClockVisualizer: React.FC<ClockSummaryProps> = ({
  clockData,
  onPause,
  onResume,
  canManageClock = false
}) => {
  const [expanded, setExpanded] = useState(false);
  const [showPauseModal, setShowPauseModal] = useState(false);
  const [pauseReason, setPauseReason] = useState('');
  const [clause, setClause] = useState('APH 2026 Cl. 4.2 (Authorized Injunction/Pause)');

  const instPercent = clockData.institution_clock.percentage || 0;
  const offPercent = clockData.official_clock.percentage || 0;

  const handlePauseSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onPause && pauseReason) {
      onPause(pauseReason, clause);
      setShowPauseModal(false);
      setPauseReason('');
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="bg-slate-900 text-white p-4 flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Clock className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-base flex items-center gap-2">
              Dual-Clock Statutory Tracking Engine
              <span className="text-xs bg-slate-800 text-blue-300 px-2 py-0.5 rounded-full font-mono">
                {clockData.rule_version}
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Separates institutional delay from official processing time under AICTE regulations.
            </p>
          </div>
        </div>

        {/* Status badges & Pause controls */}
        <div className="flex items-center gap-3">
          {clockData.status.is_paused ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
              <PauseCircle className="w-4 h-4 animate-pulse" /> CLOCK PAUSED
            </span>
          ) : clockData.status.is_active ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              ACTIVE: {clockData.status.active_clock_type} CLOCK
            </span>
          ) : (
            <span className="text-xs text-slate-400">CLOCK STOPPED (Terminal)</span>
          )}

          {canManageClock && (
            <div>
              {clockData.status.is_paused ? (
                <button
                  onClick={onResume}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-md flex items-center gap-1 cursor-pointer"
                >
                  <PlayCircle className="w-4 h-4" /> Resume Clock
                </button>
              ) : (
                <button
                  onClick={() => setShowPauseModal(true)}
                  className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-md flex items-center gap-1 cursor-pointer"
                >
                  <PauseCircle className="w-4 h-4" /> Authorize Pause
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Dual Clock Meters */}
      <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-50/50">
        {/* Institution Clock */}
        <div className={`p-4 rounded-xl border transition-all ${clockData.status.active_clock_type === 'INSTITUTION' ? 'bg-amber-50/60 border-amber-300 ring-2 ring-amber-400/20' : 'bg-white border-slate-200'}`}>
          <div className="flex justify-between items-start mb-2">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-amber-700">Clock 1</span>
              <h4 className="text-base font-semibold text-slate-800">Institution Response Clock</h4>
              <p className="text-xs text-slate-500">Drafting, clarification response, or compliance submissions</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-amber-900 font-mono">
                {clockData.institution_clock.total_days} <span className="text-xs font-normal">days</span>
              </div>
              <div className="text-xs text-slate-500 font-mono">{clockData.institution_clock.total_hours} hrs ({instPercent}%)</div>
            </div>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden mt-3">
            <div className="bg-amber-500 h-full rounded-full transition-all duration-500" style={{ width: `${Math.min(100, instPercent)}%` }} />
          </div>
        </div>

        {/* Official Clock */}
        <div className={`p-4 rounded-xl border transition-all ${clockData.status.active_clock_type === 'OFFICIAL' ? 'bg-blue-50/60 border-blue-300 ring-2 ring-blue-400/20' : 'bg-white border-slate-200'}`}>
          <div className="flex justify-between items-start mb-2">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-blue-700">Clock 2</span>
              <h4 className="text-base font-semibold text-slate-800">Official Processing Clock</h4>
              <p className="text-xs text-slate-500">Scrutiny review, EVC inspection, and regulatory decision</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-900 font-mono">
                {clockData.official_clock.total_days} <span className="text-xs font-normal">days</span>
              </div>
              <div className="text-xs text-slate-500 font-mono">{clockData.official_clock.total_hours} hrs ({offPercent}%)</div>
            </div>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden mt-3">
            <div className="bg-blue-600 h-full rounded-full transition-all duration-500" style={{ width: `${Math.min(100, offPercent)}%` }} />
          </div>
        </div>
      </div>

      {/* Total & Summary footer */}
      <div className="px-5 py-3 bg-white border-t border-slate-200 flex flex-wrap justify-between items-center gap-4 text-xs text-slate-600">
        <div className="flex items-center gap-4">
          <span><strong>Total Elapsed:</strong> {clockData.total_elapsed.total_days} days ({clockData.total_elapsed.total_hours} hours)</span>
          {clockData.paused_duration && clockData.paused_duration.total_hours > 0 && (
            <span className="text-amber-700 font-medium">
              Paused Duration Subtracted: {clockData.paused_duration.total_hours} hrs
            </span>
          )}
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 cursor-pointer"
        >
          {expanded ? 'Hide Stage Audit Breakdown' : 'View Stage Interval Breakdown'}
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Expandable Breakdown */}
      {expanded && (
        <div className="border-t border-slate-200 p-5 bg-slate-50 text-xs">
          <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg text-slate-700 flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-slate-900">How Dual-Clock Time is Calculated:</p>
              <p className="mt-0.5">{clockData.explanation}</p>
            </div>
          </div>

          <table className="w-full text-left border-collapse bg-white rounded-lg border border-slate-200 overflow-hidden">
            <thead>
              <tr className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                <th className="p-2.5">Stage</th>
                <th className="p-2.5">Attributed Clock</th>
                <th className="p-2.5">Start (UTC)</th>
                <th className="p-2.5">End (UTC)</th>
                <th className="p-2.5 text-right">Elapsed</th>
                <th className="p-2.5">Status</th>
              </tr>
            </thead>
            <tbody>
              {clockData.interval_breakdown.map((it) => (
                <tr key={it.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="p-2.5 font-medium text-slate-800">{it.stage_key}</td>
                  <td className="p-2.5">
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${it.clock_type === 'INSTITUTION' ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'}`}>
                      {it.clock_type}
                    </span>
                  </td>
                  <td className="p-2.5 font-mono text-slate-600">{new Date(it.start_time).toLocaleString()}</td>
                  <td className="p-2.5 font-mono text-slate-600">{it.end_time ? new Date(it.end_time).toLocaleString() : 'In Progress'}</td>
                  <td className="p-2.5 text-right font-mono font-medium">{it.elapsed_hours}h ({it.elapsed_days}d)</td>
                  <td className="p-2.5">
                    {it.is_paused ? (
                      <span className="text-amber-600 font-medium">Paused</span>
                    ) : it.is_active ? (
                      <span className="text-emerald-600 font-medium">Running</span>
                    ) : (
                      <span className="text-slate-400">Completed</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pause Modal */}
      {showPauseModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-2">Authorize Dual-Clock Pause</h3>
            <p className="text-xs text-slate-500 mb-4">
              Under AICTE Approval Guidelines, official and institutional clocks may only be paused with recorded administrative reasons (e.g. judicial stay, formal hearing, national holiday window).
            </p>
            <form onSubmit={handlePauseSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Regulatory Clause</label>
                <input
                  type="text"
                  value={clause}
                  onChange={(e) => setClause(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Reason for Clock Pause</label>
                <textarea
                  value={pauseReason}
                  onChange={(e) => setPauseReason(e.target.value)}
                  placeholder="Detail why statutory clock is paused..."
                  rows={3}
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPauseModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded-md text-xs font-medium text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-md text-xs font-semibold cursor-pointer"
                >
                  Confirm Pause
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
