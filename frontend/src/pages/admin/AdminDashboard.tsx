import React, { useEffect, useState } from 'react';
import { apiRequest, downloadFile } from '../../api/client';
import {
  Settings, Users, FileText, Download, Play, ShieldAlert,
  History, Building2, CheckCircle2, Clock
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export const AdminDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [schedulerStatus, setSchedulerStatus] = useState<string | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const fetchAdminData = () => {
    setLoading(true);
    apiRequest('/dashboards/admin')
      .then(setData)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleRunScheduler = async () => {
    setIsTriggering(true);
    setSchedulerStatus(null);
    try {
      const res = await apiRequest('/notifications/run-jobs', { method: 'POST' });
      setSchedulerStatus(`Background jobs executed! Created: ${res.notifications_created} notifications, Triggered: ${res.escalations_triggered} escalations.`);
      fetchAdminData();
    } catch (err: any) {
      setSchedulerStatus(`Scheduler execution error: ${err.message}`);
    } finally {
      setIsTriggering(false);
    }
  };

  const handleExportCSV = async () => {
    setIsExporting(true);
    try {
      await downloadFile('/dashboards/export/applications-csv', 'aicte_applications_export.csv');
    } catch (err: any) {
      alert(`CSV Export failed: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-xs text-slate-500">Loading system administration metrics...</div>;

  const metrics = data?.system_metrics || {};
  const regionalData = data?.regional_distribution || [];
  const auditEvents = data?.recent_audit_events || [];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap justify-between items-center gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">Central System Administration</span>
          <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">Platform Governance & Regulatory Policy</h1>
          <p className="text-xs text-slate-500 mt-1">
            Active Rule Version: <strong className="font-mono text-slate-800">{metrics.active_rule_version}</strong> • Audit Logging & Escalation Watch
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunScheduler}
            disabled={isTriggering}
            className="px-3.5 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs cursor-pointer"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{isTriggering ? 'Running Engine...' : 'Run Scheduled Escalation Job'}</span>
          </button>

          <button
            type="button"
            onClick={handleExportCSV}
            disabled={isExporting}
            className="px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs cursor-pointer disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{isExporting ? 'Exporting...' : 'Export CSV Audit Report'}</span>
          </button>
        </div>
      </div>

      {schedulerStatus && (
        <div className="p-3 bg-blue-50 border border-blue-200 text-blue-900 text-xs rounded-xl font-medium">
          {schedulerStatus}
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Registered Institutions</span>
            <Building2 className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">{metrics.total_institutions || 0}</div>
          <div className="text-[11px] text-slate-400 mt-1">Affiliated colleges</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Active Applications</span>
            <FileText className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-extrabold text-amber-900 font-mono">{metrics.active_applications || 0}</div>
          <div className="text-[11px] text-amber-700 mt-1">Under statutory workflow</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Escalated Overdue Tasks</span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-extrabold text-rose-900 font-mono">{metrics.escalations_count || 0}</div>
          <div className="text-[11px] text-rose-700 mt-1">Escalated to Bureau Authority</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Audit Events Logged</span>
            <History className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-extrabold text-emerald-900 font-mono">{metrics.total_audit_events || 0}</div>
          <div className="text-[11px] text-emerald-700 mt-1">Tamper-evident DB records</div>
        </div>
      </div>

      {/* Regional Chart & Recent Audit Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Regional Distribution */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <h3 className="font-bold text-sm text-slate-900 mb-1">Regional Dossier Pendency Distribution</h3>
          <p className="text-xs text-slate-500 mb-4">Total approval applications grouped by regional bureau jurisdiction.</p>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={regionalData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="region" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px' }} />
                <Bar dataKey="application_count" fill="#0d9488" radius={[4, 4, 0, 0]} name="Applications" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Real-time Audit Events Log */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden flex flex-col justify-between">
          <div>
            <div className="p-4 border-b border-slate-200 flex justify-between items-center">
              <h3 className="font-bold text-sm text-slate-900">Recent Regulatory Audit Events</h3>
              <span className="text-xs text-slate-400 font-mono">Live DB Stream</span>
            </div>

            <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
              {auditEvents.map((a: any) => (
                <div key={a.id} className="p-3 text-xs hover:bg-slate-50 flex justify-between items-start gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold font-mono text-blue-700">{a.action}</span>
                      <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded font-mono text-slate-600">
                        {a.entity_type} #{a.entity_id}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">By: {a.user_email}</div>
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono shrink-0">
                    {new Date(a.created_at).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
