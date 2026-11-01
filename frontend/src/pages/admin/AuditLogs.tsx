import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { History, Search, Filter } from 'lucide-react';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');

  const fetchLogs = () => {
    setLoading(true);
    let url = '/admin/audit-logs?';
    if (actionFilter) url += `action=${actionFilter}&`;
    if (entityFilter) url += `entity_type=${entityFilter}&`;

    apiRequest<{ total: number; events: any[] }>(url)
      .then((data) => {
        setLogs(data?.events || []);
        setTotal(data?.total || 0);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter, entityFilter]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex justify-between items-center">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Security & Compliance</span>
          <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">Statutory Audit Trail & Event Ledger</h1>
          <p className="text-xs text-slate-500 mt-1">
            Immutable log of state transitions, document uploads, verifications, score overrides, and clock pauses.
          </p>
        </div>
        <div className="p-3 bg-slate-100 text-slate-700 rounded-xl">
          <History className="w-6 h-6" />
        </div>
      </div>

      {/* Filter */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap gap-4 items-center">
        <div className="flex items-center gap-2 text-xs">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="font-semibold text-slate-700">Action:</span>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="text-xs p-1.5 border border-slate-300 rounded-lg bg-slate-50"
          >
            <option value="">All Actions</option>
            <option value="STAGE_TRANSITION">STAGE_TRANSITION</option>
            <option value="DOCUMENT_UPLOAD">DOCUMENT_UPLOAD</option>
            <option value="DOCUMENT_VERIFIED">DOCUMENT_VERIFIED</option>
            <option value="CLOCK_PAUSE">CLOCK_PAUSE</option>
            <option value="CLOCK_RESUME">CLOCK_RESUME</option>
            <option value="EVC_SCHEDULED">EVC_SCHEDULED</option>
            <option value="SCRUTINY_REVIEW_DECISION">SCRUTINY_REVIEW_DECISION</option>
          </select>
        </div>

        <div className="text-xs text-slate-500 ml-auto font-mono">
          Total Recorded Events: <strong>{total}</strong>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th className="p-3.5">Timestamp (UTC)</th>
                <th className="p-3.5">Action</th>
                <th className="p-3.5">Entity</th>
                <th className="p-3.5">Actor</th>
                <th className="p-3.5">Audit Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={5} className="p-8 text-center text-slate-400">Loading audit trail...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={5} className="p-8 text-center text-slate-400">No audit events match filters.</td></tr>
              ) : (
                logs.map((e) => (
                  <tr key={e.id} className="hover:bg-slate-50">
                    <td className="p-3.5 font-mono text-slate-500 whitespace-nowrap">
                      {new Date(e.created_at).toLocaleString()}
                    </td>
                    <td className="p-3.5">
                      <span className="px-2 py-0.5 rounded font-mono font-bold text-[10px] bg-blue-50 text-blue-800 border border-blue-200">
                        {e.action}
                      </span>
                    </td>
                    <td className="p-3.5 font-mono text-slate-700 font-semibold">
                      {e.entity_type} #{e.entity_id}
                    </td>
                    <td className="p-3.5 text-slate-600 font-mono text-[11px]">{e.user_email}</td>
                    <td className="p-3.5 font-mono text-[11px] text-slate-600 max-w-md truncate">
                      {JSON.stringify(e.details)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
