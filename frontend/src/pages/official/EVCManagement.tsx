import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { CalendarCheck, Plus, AlertTriangle, CheckCircle2, FileText, UserPlus, Upload } from 'lucide-react';

export const EVCManagement: React.FC = () => {
  const [visits, setVisits] = useState<any[]>([]);
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Scheduling Form Modal
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedAppId, setSelectedAppId] = useState('');
  const [proposedDate, setProposedDate] = useState('');
  const [officerName, setOfficerName] = useState('');
  const [officerEmail, setOfficerEmail] = useState('');
  const [officers, setOfficers] = useState<Array<{ name: string; email: string }>>([]);
  const [scheduleError, setScheduleError] = useState('');

  // Report Modal
  const [activeVisitForReport, setActiveVisitForReport] = useState<any | null>(null);
  const [visitOutcome, setVisitOutcome] = useState('RECOMMENDED');
  const [reportSummary, setReportSummary] = useState('');
  const [deficiencies, setDeficiencies] = useState('');
  const [followUpRequired, setFollowUpRequired] = useState(false);

  const fetchVisitsAndApps = async () => {
    setLoading(true);
    try {
      const [vData, aData] = await Promise.all([
        apiRequest<any[]>('/evc'),
        apiRequest<any[]>('/applications?stage=EVC_SCHEDULED')
      ]);
      setVisits(vData || []);
      setApplications(aData || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVisitsAndApps();
  }, []);

  const handleAddOfficer = () => {
    if (officerName && officerEmail) {
      setOfficers([...officers, { name: officerName, email: officerEmail }]);
      setOfficerName('');
      setOfficerEmail('');
    }
  };

  const handleScheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppId || !proposedDate || officers.length === 0) {
      setScheduleError('Please fill in application, proposed date, and at least one committee officer.');
      return;
    }
    setScheduleError('');

    try {
      await apiRequest('/evc/schedule', {
        method: 'POST',
        body: JSON.stringify({
          application_id: parseInt(selectedAppId),
          proposed_date: new Date(proposedDate).toISOString(),
          assigned_officers: officers
        })
      });
      setShowScheduleModal(false);
      setOfficers([]);
      setSelectedAppId('');
      setProposedDate('');
      fetchVisitsAndApps();
    } catch (err: any) {
      setScheduleError(err.message || 'Scheduling failed.');
    }
  };

  const handleToggleChecklistItem = async (visit: any, index: number) => {
    const updatedChecklist = [...(visit.preparation_checklist || [])];
    updatedChecklist[index].completed = !updatedChecklist[index].completed;

    try {
      await apiRequest(`/evc/${visit.id}/checklist`, {
        method: 'PUT',
        body: JSON.stringify(updatedChecklist)
      });
      fetchVisitsAndApps();
    } catch (err: any) {
      alert(`Error updating checklist: ${err.message}`);
    }
  };

  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeVisitForReport) return;

    const formData = new FormData();
    formData.append('visit_outcome', visitOutcome);
    formData.append('report_summary', reportSummary);
    formData.append('deficiencies_found', deficiencies);
    formData.append('follow_up_required', String(followUpRequired));

    try {
      await apiRequest(`/evc/${activeVisitForReport.id}/report`, {
        method: 'POST',
        body: formData
      });
      setActiveVisitForReport(null);
      setReportSummary('');
      setDeficiencies('');
      fetchVisitsAndApps();
    } catch (err: any) {
      alert(`Report error: ${err.message}`);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap justify-between items-center gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-amber-700">Physical Verification Module</span>
          <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">Expert Visiting Committee (EVC) Operations</h1>
          <p className="text-xs text-slate-500 mt-1">
            Schedule physical inspection panels, verify officer availability without conflicts, and record visit outcomes.
          </p>
        </div>
        <button
          onClick={() => setShowScheduleModal(true)}
          className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center gap-2 cursor-pointer"
        >
          <Plus className="w-4 h-4" /> Schedule New EVC Inspection
        </button>
      </div>

      {/* Visits List */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading EVC inspections...</div>
        ) : visits.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500 bg-white rounded-2xl border border-slate-200">
            No EVC visits scheduled.
          </div>
        ) : (
          visits.map((v) => (
            <div key={v.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
              <div className="flex flex-wrap justify-between items-start gap-4 border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-base text-slate-900 font-mono">{v.visit_reference}</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                      v.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' :
                      v.status === 'SCHEDULED' ? 'bg-amber-100 text-amber-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {v.status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    Proposed Inspection Date: <strong className="text-slate-800 font-mono">{new Date(v.proposed_date).toLocaleDateString()}</strong>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {v.status !== 'COMPLETED' && (
                    <button
                      onClick={() => setActiveVisitForReport(v)}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1 cursor-pointer"
                    >
                      <Upload className="w-3.5 h-3.5" /> Submit Inspection Outcome
                    </button>
                  )}
                  {v.visit_outcome && (
                    <span className={`px-3 py-1 rounded-lg text-xs font-bold ${
                      v.visit_outcome === 'RECOMMENDED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' :
                      'bg-rose-100 text-rose-800 border border-rose-300'
                    }`}>
                      Outcome: {v.visit_outcome}
                    </span>
                  )}
                </div>
              </div>

              {/* Committee Members */}
              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Assigned Inspection Committee</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {(v.assigned_officers || []).map((o: any, idx: number) => (
                    <div key={idx} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                      <div className="font-bold text-slate-800">{o.name}</div>
                      <div className="text-slate-500 text-[11px] font-mono">{o.email}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Inspection Checklist */}
              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Statutory Inspection Checklist</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {(v.preparation_checklist || []).map((item: any, i: number) => (
                    <label key={i} className="flex items-start gap-2.5 p-2 bg-slate-50 rounded-lg border border-slate-200 text-xs cursor-pointer hover:bg-slate-100">
                      <input
                        type="checkbox"
                        checked={item.completed}
                        onChange={() => handleToggleChecklistItem(v, i)}
                        className="mt-0.5 rounded text-blue-600"
                      />
                      <span className={item.completed ? 'line-through text-slate-400' : 'text-slate-800 font-medium'}>
                        {item.item}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Visit Outcome & Deficiencies if completed */}
              {v.report_summary && (
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
                  <div className="font-bold text-slate-800">EVC Executive Report Summary:</div>
                  <p className="text-slate-600">{v.report_summary}</p>
                  {v.deficiencies_found && v.deficiencies_found.length > 0 && (
                    <div className="pt-2 text-rose-700">
                      <strong>Deficiencies Noted: </strong>{v.deficiencies_found.join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Schedule Modal */}
      {showScheduleModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Schedule EVC Physical Inspection</h3>
            <p className="text-xs text-slate-500 mb-4">Conflict detection automatically validates officer calendars.</p>

            {scheduleError && <div className="mb-3 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">{scheduleError}</div>}

            <form onSubmit={handleScheduleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Application</label>
                <select
                  value={selectedAppId}
                  onChange={(e) => setSelectedAppId(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                  required
                >
                  <option value="">-- Choose Dossier --</option>
                  {applications.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.application_number} ({a.institution_name})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Proposed Inspection Date</label>
                <input
                  type="date"
                  value={proposedDate}
                  onChange={(e) => setProposedDate(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                  required
                />
              </div>

              {/* Committee Members builder */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <span className="text-xs font-bold text-slate-800">Assign Committee Members</span>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={officerName}
                    onChange={(e) => setOfficerName(e.target.value)}
                    placeholder="Officer Name"
                    className="text-xs p-2 border border-slate-300 rounded-lg bg-white"
                  />
                  <input
                    type="email"
                    value={officerEmail}
                    onChange={(e) => setOfficerEmail(e.target.value)}
                    placeholder="officer@aicte.gov.in"
                    className="text-xs p-2 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleAddOfficer}
                  className="text-xs px-3 py-1 bg-slate-800 text-white rounded font-semibold cursor-pointer"
                >
                  + Add Officer to Panel
                </button>

                {officers.length > 0 && (
                  <div className="space-y-1 pt-2">
                    {officers.map((o, i) => (
                      <div key={i} className="text-xs p-1.5 bg-white rounded border border-slate-200 flex justify-between">
                        <span>{o.name} ({o.email})</span>
                        <button
                          type="button"
                          onClick={() => setOfficers(officers.filter((_, idx) => idx !== i))}
                          className="text-red-600 font-bold"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowScheduleModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  Confirm & Check Conflicts
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Report Submission Modal */}
      {activeVisitForReport && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Submit EVC Inspection Findings</h3>
            <p className="text-xs text-slate-500 mb-4">Visit Ref: {activeVisitForReport.visit_reference}</p>

            <form onSubmit={handleReportSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Panel Outcome Recommendation</label>
                <select
                  value={visitOutcome}
                  onChange={(e) => setVisitOutcome(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                >
                  <option value="RECOMMENDED">RECOMMENDED (Meets AICTE Norms)</option>
                  <option value="DEFICIENCIES_NOTED">DEFICIENCIES_NOTED (Conditional Approval)</option>
                  <option value="REJECTED">REJECTED (Infrastructure Inadequate)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Inspection Summary</label>
                <textarea
                  rows={3}
                  value={reportSummary}
                  onChange={(e) => setReportSummary(e.target.value)}
                  placeholder="Record verification of labs, library, Divyangjan access, fire clearance..."
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Deficiencies (Comma separated)</label>
                <input
                  type="text"
                  value={deficiencies}
                  onChange={(e) => setDeficiencies(e.target.value)}
                  placeholder="e.g. Inadequate chemistry lab exhaust, Library lacks 50 mandatory titles"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                />
              </div>

              <label className="flex items-center gap-2 text-xs font-medium cursor-pointer">
                <input
                  type="checkbox"
                  checked={followUpRequired}
                  onChange={(e) => setFollowUpRequired(e.target.checked)}
                />
                <span>Mandate compliance undertaking / 15-day follow up visit</span>
              </label>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setActiveVisitForReport(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  Submit Formal Report
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
