import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { Link } from 'react-router-dom';
import {
  FileText, Clock, AlertCircle, CheckCircle2, XCircle, ArrowRight,
  ShieldCheck, AlertTriangle, Calendar
} from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';

export const InstitutionDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest('/dashboards/institution')
      .then(setData)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-500 text-xs">
        Loading institutional dashboard data...
      </div>
    );
  }

  const metrics = data?.metrics || {};
  const stageDist = data?.stage_distribution || {};

  const chartData = [
    { name: 'In Progress', value: metrics.in_progress || 0, color: '#3b82f6' },
    { name: 'Approved', value: metrics.approved || 0, color: '#10b981' },
    { name: 'Rejected', value: metrics.rejected || 0, color: '#ef4444' },
    { name: 'Clarifications', value: metrics.pending_clarifications || 0, color: '#f59e0b' },
  ].filter(d => d.value > 0);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-wrap justify-between items-center gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-blue-700">Institution Portal</span>
          <h1 className="text-2xl font-extrabold text-slate-900 mt-0.5">Approval & Compliance Dashboard</h1>
          <p className="text-xs text-slate-500 mt-1">
            Track statutory approval applications, responses to clarification requests, and compliance undertakings.
          </p>
        </div>
        <Link
          to="/institution/applications/new"
          className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center gap-2 cursor-pointer"
        >
          <span>Initiate New Application</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Critical Action Banner if clarification required or compliance overdue */}
      {(metrics.pending_clarifications > 0 || metrics.overdue_compliance > 0) && (
        <div className="p-4 bg-amber-50 border border-amber-300 rounded-xl flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-900 flex-1">
            <h4 className="font-bold">Attention Required: Institution Clock is Active</h4>
            <p className="mt-0.5 text-amber-800">
              You have <strong>{metrics.pending_clarifications} application(s)</strong> awaiting clarification response and{' '}
              <strong>{metrics.overdue_compliance} compliance undertaking(s)</strong> overdue. Institutional clock is accumulating.
            </p>
          </div>
        </div>
      )}

      {/* Key Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Total Applications</span>
            <FileText className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">{metrics.total_applications || 0}</div>
          <div className="text-[11px] text-slate-400 mt-1">{metrics.in_progress || 0} currently under scrutiny</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Clarifications Needed</span>
            <AlertCircle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-extrabold text-amber-900 font-mono">{metrics.pending_clarifications || 0}</div>
          <div className="text-[11px] text-amber-700 mt-1">Requires institutional action</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Pending Undertakings</span>
            <CheckCircle2 className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-extrabold text-purple-900 font-mono">{metrics.pending_compliance || 0}</div>
          <div className="text-[11px] text-purple-700 mt-1">{metrics.overdue_compliance || 0} overdue items</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Expiring Certificates</span>
            <Clock className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-extrabold text-rose-900 font-mono">{metrics.expiring_documents || 0}</div>
          <div className="text-[11px] text-rose-700 mt-1">Expires within 60 days</div>
        </div>
      </div>

      {/* Charts & Applications List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Recent Applications Table */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-200 flex justify-between items-center">
            <h3 className="font-bold text-sm text-slate-900">Recent Applications</h3>
            <Link to="/institution/applications" className="text-xs font-semibold text-blue-600 hover:text-blue-800">
              View All Applications →
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold">
                <tr>
                  <th className="p-3">Application Number</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Current Stage</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(data?.recent_applications || []).length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-4 text-center text-slate-400">
                      No applications found. Click "Initiate New Application" to begin.
                    </td>
                  </tr>
                ) : (
                  data.recent_applications.map((app: any) => (
                    <tr key={app.id} className="hover:bg-slate-50 transition-colors">
                      <td className="p-3 font-bold text-blue-600 font-mono">{app.application_number}</td>
                      <td className="p-3 text-slate-700">{app.application_type.replace(/_/g, ' ')}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
                          {app.current_stage}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          app.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' :
                          app.status === 'REJECTED' ? 'bg-rose-100 text-rose-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {app.status}
                        </span>
                      </td>
                      <td className="p-3 text-right">
                        <Link
                          to={`/institution/applications/${app.id}`}
                          className="px-2.5 py-1 bg-slate-100 hover:bg-blue-600 hover:text-white rounded text-slate-700 font-semibold transition-colors"
                        >
                          View Details
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Pie Distribution */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-sm text-slate-900 mb-1">Application Status Overview</h3>
            <p className="text-xs text-slate-500 mb-4">Real-time status breakdown from database records.</p>
            {chartData.length === 0 ? (
              <div className="h-44 flex items-center justify-center text-xs text-slate-400">No chart data</div>
            ) : (
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={chartData} innerRadius={45} outerRadius={70} paddingAngle={4} dataKey="value">
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          <div className="space-y-1.5 border-t border-slate-100 pt-3 text-xs">
            {chartData.map((d, i) => (
              <div key={i} className="flex justify-between items-center text-slate-600">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                  <span>{d.name}</span>
                </div>
                <span className="font-mono font-bold text-slate-800">{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
