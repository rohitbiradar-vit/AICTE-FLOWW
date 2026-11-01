import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { Link } from 'react-router-dom';
import {
  FileText, Clock, AlertTriangle, CalendarCheck, CheckSquare,
  ShieldAlert, ArrowRight, TrendingUp, Layers
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export const OfficialDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest('/dashboards/official')
      .then(setData)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-500">Loading scrutiny bureau analytics...</div>;
  }

  const bottlenecks = (data?.bottlenecks || []).map((b: any) => ({
    stage: b.stage_key.replace(/_/g, ' '),
    hours: b.average_hours,
    count: b.interval_count
  }));

  const clockAvg = data?.clock_averages || { institution_clock_avg_hours: 0, official_clock_avg_hours: 0 };
  const highPriorityCases = data?.high_priority_cases || [];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-blue-700">AICTE Regulation Bureau</span>
          <h1 className="text-2xl font-extrabold text-slate-900 mt-0.5">Scrutiny & Operational Command Center</h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time regulatory workload, statutory processing clocks, bottleneck detection, and high-priority triage.
          </p>
        </div>
        <Link
          to="/official/work-queue"
          className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center gap-2 cursor-pointer"
        >
          <span>Open Assigned Work Queue</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Active Work Queue</span>
            <FileText className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">{data?.work_queue_count || 0}</div>
          <div className="text-[11px] text-slate-400 mt-1">Dossiers under processing</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Overdue Tasks</span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-extrabold text-rose-900 font-mono">{data?.overdue_count || 0}</div>
          <div className="text-[11px] text-rose-700 mt-1">Exceeded SLA threshold</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Pending EVC Visits</span>
            <CalendarCheck className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-extrabold text-amber-900 font-mono">{data?.pending_evc_visits || 0}</div>
          <div className="text-[11px] text-amber-700 mt-1">Scheduled or awaiting report</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Compliance Verifications</span>
            <CheckSquare className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-extrabold text-purple-900 font-mono">{data?.compliance_queue_count || 0}</div>
          <div className="text-[11px] text-purple-700 mt-1">Evidence awaiting officer sign-off</div>
        </div>
      </div>

      {/* Dual-Clock Aggregate Ratio Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 shadow-md">
        <div className="flex flex-wrap justify-between items-center gap-4 mb-4">
          <div>
            <h3 className="text-base font-bold flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-400" />
              Statutory Dual-Clock Processing Ratio (System-wide Average)
            </h3>
            <p className="text-xs text-slate-300 mt-0.5">
              Empirical calculation attributing delay between institution response time vs official AICTE statutory scrutiny.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-800/80 rounded-xl border border-slate-700">
            <span className="text-xs font-semibold text-amber-400 uppercase">Average Institution Response Time</span>
            <div className="text-2xl font-bold font-mono mt-1 text-white">
              {clockAvg.institution_clock_avg_hours} <span className="text-xs font-normal text-slate-400">hours</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Time spent by colleges compiling evidence & responding to clarification notices</p>
          </div>

          <div className="p-4 bg-slate-800/80 rounded-xl border border-slate-700">
            <span className="text-xs font-semibold text-blue-400 uppercase">Average Official Scrutiny Time</span>
            <div className="text-2xl font-bold font-mono mt-1 text-white">
              {clockAvg.official_clock_avg_hours} <span className="text-xs font-normal text-slate-400">hours</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Time spent by AICTE scrutiny officers, EVC inspection teams, and regional committees</p>
          </div>
        </div>
      </div>

      {/* Bottlenecks Chart & High Priority Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stage Bottleneck Analysis */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-sm text-slate-900 mb-1 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-600" />
              Workflow Stage Duration & Bottleneck Detection
            </h3>
            <p className="text-xs text-slate-500 mb-4">Average hours applications spend in each regulatory stage.</p>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={bottlenecks} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="stage" tick={{ fontSize: 9 }} angle={-20} textAnchor="end" height={40} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px' }} />
                  <Bar dataKey="hours" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Average Hours" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* High Priority Scrutiny Cases */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden flex flex-col justify-between">
          <div>
            <div className="p-4 border-b border-slate-200 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-red-600" />
                  High-Priority Scrutiny Triage Queue
                </h3>
                <p className="text-[11px] text-slate-500">Cases requiring priority attention due to missing docs or expired certificates.</p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800">
                Score ≥ 75
              </span>
            </div>

            <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
              {highPriorityCases.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400">
                  No high-priority scrutiny alerts at this time.
                </div>
              ) : (
                highPriorityCases.map((c: any) => (
                  <div key={c.report_id} className="p-3.5 hover:bg-slate-50 text-xs flex justify-between items-start gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-blue-600 font-mono">{c.application_number}</span>
                        <span className="font-bold text-slate-900">{c.institution_name}</span>
                      </div>
                      <div className="text-[11px] text-slate-600 mt-1">
                        Deficiencies: {c.missing_docs_count} missing doc(s), {c.inconsistencies_count} data mismatch(es), {c.expired_docs_count} expired.
                      </div>
                      <div className="text-[10px] text-slate-500 italic mt-0.5">{c.suggested_action}</div>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="px-2 py-0.5 rounded bg-red-100 text-red-800 font-mono font-bold text-xs block mb-1">
                        Score {c.priority_score}
                      </span>
                      <Link
                        to={`/official/applications/${c.application_id}`}
                        className="text-[11px] font-semibold text-blue-600 hover:underline"
                      >
                        Inspect →
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
