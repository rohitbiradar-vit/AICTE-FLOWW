import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { Link } from 'react-router-dom';
import { FileText, Search, Filter, ShieldAlert, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';

export const WorkQueue: React.FC = () => {
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [stageFilter, setStageFilter] = useState('');
  const [search, setSearch] = useState('');

  const fetchQueue = () => {
    setLoading(true);
    let url = '/applications?';
    if (stageFilter) url += `stage=${stageFilter}&`;
    if (search) url += `search=${encodeURIComponent(search)}&`;

    apiRequest<any[]>(url)
      .then((data) => setApplications(data || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchQueue();
  }, [stageFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchQueue();
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex justify-between items-center">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-blue-700">Official Work Queue</span>
          <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">Assigned Regulatory Dossiers</h1>
          <p className="text-xs text-slate-500 mt-1">
            Review submitted institutional dossiers, verify documents, and record stage decisions.
          </p>
        </div>
        <div className="p-3 bg-blue-50 text-blue-800 rounded-xl">
          <FileText className="w-6 h-6" />
        </div>
      </div>

      {/* Filter and Search */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap justify-between items-center gap-3">
        <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search application number or institution..."
              className="w-full text-xs pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800"
            />
          </div>
          <button type="submit" className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg cursor-pointer">
            Search
          </button>
        </form>

        <div className="flex items-center gap-2 text-xs">
          <Filter className="w-4 h-4 text-slate-500" />
          <span className="font-semibold text-slate-700">Filter Stage:</span>
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="text-xs p-1.5 border border-slate-200 rounded-lg bg-slate-50 font-medium cursor-pointer"
          >
            <option value="">All Stages</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="INITIAL_SCRUTINY">Initial Scrutiny</option>
            <option value="CLARIFICATION_REQUIRED">Clarification Required</option>
            <option value="RESUBMITTED">Clarification Resubmitted</option>
            <option value="EVC_SCHEDULED">EVC Scheduled</option>
            <option value="COMMITTEE_REVIEW">Committee Review</option>
            <option value="FINAL_APPROVAL">Final Approval</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th className="p-3.5">Application #</th>
                <th className="p-3.5">Institution Name</th>
                <th className="p-3.5">Type & Session</th>
                <th className="p-3.5">Current Stage</th>
                <th className="p-3.5">Deadline</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={6} className="p-8 text-center text-slate-400">Loading work queue...</td></tr>
              ) : applications.length === 0 ? (
                <tr><td colSpan={6} className="p-8 text-center text-slate-400">No applications found in this queue.</td></tr>
              ) : (
                applications.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50 transition-colors">
                    <td className="p-3.5 font-bold font-mono text-blue-600">{app.application_number}</td>
                    <td className="p-3.5 font-semibold text-slate-800">{app.institution_name}</td>
                    <td className="p-3.5 text-slate-600">
                      <div>{app.application_type.replace(/_/g, ' ')}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{app.academic_year}</div>
                    </td>
                    <td className="p-3.5">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
                        {app.current_stage_key.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="p-3.5 font-mono text-slate-600">
                      {app.current_deadline ? (
                        <span className={new Date(app.current_deadline) < new Date() ? 'text-red-600 font-bold' : ''}>
                          {new Date(app.current_deadline).toLocaleDateString()}
                        </span>
                      ) : 'N/A'}
                    </td>
                    <td className="p-3.5 text-right">
                      <Link
                        to={`/official/applications/${app.id}`}
                        className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs inline-flex items-center gap-1 shadow-xs cursor-pointer"
                      >
                        Inspect Dossier <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
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
