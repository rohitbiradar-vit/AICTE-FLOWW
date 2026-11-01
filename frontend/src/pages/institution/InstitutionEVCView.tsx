import React, { useEffect, useState } from 'react';
import { apiRequest, downloadFile } from '../../api/client';
import {
  CalendarCheck,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Download,
  Users,
  FileText,
  CheckSquare,
  Info,
  Calendar,
  AlertCircle
} from 'lucide-react';

interface AssignedOfficer {
  name: string;
  email: string;
  designation?: string;
  role?: string;
}

interface ChecklistItem {
  item: string;
  completed?: boolean;
  notes?: string;
}

interface EVCVisit {
  id: number;
  visit_reference: string;
  application_id: number;
  institution_id: number;
  application_number?: string;
  institution_name?: string;
  proposed_date: string;
  confirmed_date?: string;
  status: string;
  assigned_officers: AssignedOfficer[];
  preparation_checklist: ChecklistItem[];
  visit_outcome?: string;
  report_filename?: string;
  report_summary?: string;
  deficiencies_found: string[];
  follow_up_required: boolean;
  follow_up_deadline?: string;
  conducted_at?: string;
  created_at: string;
}

export const InstitutionEVCView: React.FC = () => {
  const [visits, setVisits] = useState<EVCVisit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  const fetchVisits = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiRequest<EVCVisit[]>('/evc');
      setVisits(data || []);
    } catch (err: any) {
      console.error('Failed to load EVC visits:', err);
      setError(err.message || 'Failed to load EVC schedule. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVisits();
  }, []);

  const handleDownloadReport = async (visitId: number, filename?: string) => {
    setDownloadingId(visitId);
    try {
      await downloadFile(`/evc/${visitId}/download-report`, filename || `evc_report_${visitId}.pdf`);
    } catch (err: any) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setDownloadingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" /> Completed
          </span>
        );
      case 'SCHEDULED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
            <Clock className="w-3.5 h-3.5" /> Scheduled
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
            <Clock className="w-3.5 h-3.5" /> In Progress
          </span>
        );
      case 'REPORT_SUBMITTED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-200">
            <FileText className="w-3.5 h-3.5" /> Report Submitted
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200">
            <XCircle className="w-3.5 h-3.5" /> Cancelled
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  const getOutcomeBadge = (outcome: string) => {
    switch (outcome) {
      case 'RECOMMENDED':
        return (
          <span className="px-2.5 py-1 rounded text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            RECOMMENDED FOR APPROVAL
          </span>
        );
      case 'DEFICIENCIES_NOTED':
        return (
          <span className="px-2.5 py-1 rounded text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
            DEFICIENCIES NOTED
          </span>
        );
      case 'REJECTED':
        return (
          <span className="px-2.5 py-1 rounded text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
            NOT RECOMMENDED / REJECTED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded text-xs font-bold bg-slate-50 text-slate-700 border border-slate-200">
            {outcome}
          </span>
        );
    }
  };

  const filteredVisits = visits.filter((v) => {
    if (statusFilter === 'ALL') return true;
    if (statusFilter === 'UPCOMING') return v.status === 'SCHEDULED' || v.status === 'IN_PROGRESS' || v.status === 'REQUESTED';
    if (statusFilter === 'COMPLETED') return v.status === 'COMPLETED' || v.status === 'REPORT_SUBMITTED';
    if (statusFilter === 'CANCELLED') return v.status === 'CANCELLED';
    return true;
  });

  const totalCount = visits.length;
  const upcomingCount = visits.filter(v => v.status === 'SCHEDULED' || v.status === 'IN_PROGRESS' || v.status === 'REQUESTED').length;
  const completedCount = visits.filter(v => v.status === 'COMPLETED' || v.status === 'REPORT_SUBMITTED').length;
  const actionRequiredCount = visits.filter(v => v.follow_up_required && v.status === 'COMPLETED').length;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">Expert Visit Committee (EVC) Portal</span>
          <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">Physical Inspection Schedule & Reports</h1>
          <p className="text-sm text-slate-500 mt-1">
            Track scheduled peer verification visits, expert panel members, readiness checklists, and official inspection reports.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchVisits}
            className="px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Total Visits</span>
            <CalendarCheck className="w-5 h-5 text-indigo-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{totalCount}</p>
          <span className="text-xs text-slate-400 mt-1 block">Scheduled or completed inspections</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Upcoming / Active</span>
            <Clock className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-blue-700 mt-2">{upcomingCount}</p>
          <span className="text-xs text-slate-400 mt-1 block">Awaiting or in progress</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Completed Visits</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-emerald-700 mt-2">{completedCount}</p>
          <span className="text-xs text-slate-400 mt-1 block">Reports submitted & finalized</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Follow-up Required</span>
            <AlertTriangle className="w-5 h-5 text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-amber-700 mt-2">{actionRequiredCount}</p>
          <span className="text-xs text-slate-400 mt-1 block">Deficiencies needing rectification</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
        {(['ALL', 'UPCOMING', 'COMPLETED', 'CANCELLED'] as const).map((filter) => (
          <button
            key={filter}
            onClick={() => setStatusFilter(filter)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              statusFilter === filter
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {filter === 'ALL' && `All (${totalCount})`}
            {filter === 'UPCOMING' && `Upcoming (${upcomingCount})`}
            {filter === 'COMPLETED' && `Completed (${completedCount})`}
            {filter === 'CANCELLED' && 'Cancelled'}
          </button>
        ))}
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent mb-3" />
          <p className="text-sm font-medium text-slate-600">Loading your EVC inspection schedule...</p>
        </div>
      ) : error ? (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-center">
          <AlertCircle className="w-8 h-8 text-rose-600 mx-auto mb-2" />
          <h3 className="text-base font-bold text-rose-900">Failed to load EVC schedule</h3>
          <p className="text-sm text-rose-700 mt-1">{error}</p>
          <button
            onClick={fetchVisits}
            className="mt-4 px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      ) : filteredVisits.length === 0 ? (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center space-y-3">
          <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mx-auto">
            <Calendar className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800">No EVC Visits Found</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            {statusFilter === 'ALL'
              ? 'No Expert Visit Committee (EVC) inspections have been scheduled for your institution yet. When an inspection is assigned by AICTE Regional Office, it will appear here.'
              : `There are currently no visits matching the '${statusFilter.toLowerCase()}' filter.`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredVisits.map((visit) => {
            const visitDate = visit.confirmed_date || visit.proposed_date;
            const formattedDate = visitDate
              ? new Date(visitDate).toLocaleDateString('en-IN', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric',
                  weekday: 'short',
                })
              : 'Date Pending';

            const checklistDone = (visit.preparation_checklist || []).filter((c) => c.completed).length;
            const checklistTotal = (visit.preparation_checklist || []).length;
            const canDownloadReport =
              (visit.status === 'COMPLETED' || visit.status === 'REPORT_SUBMITTED') &&
              Boolean(visit.report_filename);

            return (
              <div
                key={visit.id}
                className="bg-white rounded-2xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all p-6 space-y-5"
              >
                {/* Header row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-base font-bold text-indigo-900 bg-indigo-50 px-3 py-1 rounded-lg border border-indigo-100">
                      {visit.visit_reference}
                    </span>
                    {getStatusBadge(visit.status)}
                    {visit.visit_outcome && getOutcomeBadge(visit.visit_outcome)}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="font-semibold text-slate-700">Scheduled Date:</span>
                    <span className="bg-slate-100 text-slate-800 px-2.5 py-1 rounded font-medium">
                      {formattedDate}
                    </span>
                  </div>
                </div>

                {/* Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Column 1: Application info */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
                      Application Reference
                    </span>
                    <p className="text-sm font-bold text-slate-900">
                      {visit.application_number || `Application #${visit.application_id}`}
                    </p>
                    {visit.institution_name && (
                      <p className="text-xs text-slate-600">{visit.institution_name}</p>
                    )}
                    <span className="text-xs text-slate-400 block pt-1">
                      Initiated: {new Date(visit.created_at).toLocaleDateString('en-IN')}
                    </span>
                  </div>

                  {/* Column 2: Committee panel */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5" /> Assigned Inspection Committee
                    </span>
                    {visit.assigned_officers && visit.assigned_officers.length > 0 ? (
                      <div className="space-y-1.5">
                        {visit.assigned_officers.map((officer, idx) => (
                          <div key={idx} className="text-xs bg-slate-50 p-2 rounded-lg border border-slate-100">
                            <span className="font-bold text-slate-800 block">{officer.name}</span>
                            <span className="text-slate-500">{officer.email}</span>
                            {officer.designation && (
                              <span className="text-slate-400 block text-[11px]">{officer.designation}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic">Committee panel being constituted</p>
                    )}
                  </div>

                  {/* Column 3: Readiness checklist progress */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
                      <CheckSquare className="w-3.5 h-3.5" /> Inspection Readiness Checklist
                    </span>
                    {checklistTotal > 0 ? (
                      <div>
                        <div className="flex justify-between items-center text-xs text-slate-600 mb-1">
                          <span>Verification Items</span>
                          <span className="font-bold">
                            {checklistDone} of {checklistTotal} verified
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-2 rounded-full transition-all ${
                              checklistDone === checklistTotal ? 'bg-emerald-500' : 'bg-indigo-600'
                            }`}
                            style={{
                              width: `${(checklistDone / checklistTotal) * 100}%`,
                            }}
                          />
                        </div>
                        <div className="mt-2 space-y-1 max-h-28 overflow-y-auto pr-1">
                          {visit.preparation_checklist.map((item, idx) => (
                            <div key={idx} className="flex items-start gap-1.5 text-xs text-slate-600">
                              {item.completed ? (
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                              ) : (
                                <div className="w-3.5 h-3.5 rounded-full border border-slate-300 shrink-0 mt-0.5" />
                              )}
                              <span className={item.completed ? 'line-through text-slate-400' : ''}>
                                {item.item}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic">No checklist items defined</p>
                    )}
                  </div>
                </div>

                {/* Report & Deficiencies section if completed */}
                {(visit.report_summary || (visit.deficiencies_found && visit.deficiencies_found.length > 0) || canDownloadReport) && (
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-indigo-700" />
                        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                          Inspection Findings & Report
                        </h4>
                      </div>
                      {canDownloadReport && (
                        <button
                          onClick={() => handleDownloadReport(visit.id, visit.report_filename)}
                          disabled={downloadingId === visit.id}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg shadow-xs transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" />
                          {downloadingId === visit.id ? 'Downloading...' : 'Download EVC Inspection Report'}
                        </button>
                      )}
                    </div>

                    {visit.report_summary && (
                      <p className="text-xs text-slate-700 leading-relaxed bg-white p-3 rounded-lg border border-slate-200">
                        {visit.report_summary}
                      </p>
                    )}

                    {visit.deficiencies_found && visit.deficiencies_found.length > 0 && (
                      <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 space-y-1.5">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-rose-800">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>Deficiencies Noted by Inspection Committee:</span>
                        </div>
                        <ul className="list-disc list-inside text-xs text-rose-700 space-y-0.5 pl-1">
                          {visit.deficiencies_found.map((def, idx) => (
                            <li key={idx}>{def}</li>
                          ))}
                        </ul>
                        {visit.follow_up_required && visit.follow_up_deadline && (
                          <div className="text-xs font-semibold text-rose-900 pt-1">
                            Rectification / Compliance Due By:{' '}
                            <span className="underline">
                              {new Date(visit.follow_up_deadline).toLocaleDateString('en-IN', {
                                day: 'numeric',
                                month: 'short',
                                year: 'numeric',
                              })}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Inspection pending notice if not completed */}
                {visit.status !== 'COMPLETED' && visit.status !== 'REPORT_SUBMITTED' && (
                  <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 px-3 py-2 rounded-lg border border-slate-100">
                    <Info className="w-4 h-4 text-indigo-500 shrink-0" />
                    <span>
                      The inspection report and outcome will be made available for download here immediately after the committee conducts the visit and submits their finalized verification findings.
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
export default InstitutionEVCView;
