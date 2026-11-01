import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { CheckSquare, Upload, AlertCircle, Clock, CheckCircle2, XCircle } from 'lucide-react';

export const CompliancePortal: React.FC = () => {
  const [undertakings, setUndertakings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUt, setSelectedUt] = useState<any | null>(null);
  const [evidenceDesc, setEvidenceDesc] = useState('');
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [msg, setMsg] = useState('');

  const fetchUndertakings = () => {
    setLoading(true);
    apiRequest<any[]>('/compliance/undertakings')
      .then((data) => setUndertakings(data || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchUndertakings();
  }, []);

  const handleEvidenceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUt || !evidenceFile) return;

    setIsSubmitting(true);
    setMsg('');

    const formData = new FormData();
    formData.append('file', evidenceFile);
    formData.append('evidence_description', evidenceDesc);

    try {
      await apiRequest(`/compliance/undertakings/${selectedUt.id}/submit-evidence`, {
        method: 'POST',
        body: formData
      });
      setMsg('Compliance evidence submitted successfully! Assigned for officer verification.');
      setSelectedUt(null);
      setEvidenceFile(null);
      setEvidenceDesc('');
      fetchUndertakings();
    } catch (err: any) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex justify-between items-center">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-purple-700">Statutory Compliance Portal</span>
          <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">Time-Bound Regulatory Undertakings</h1>
          <p className="text-xs text-slate-500 mt-1">
            Monitor conditional approvals, time-bound commitments, and upload verified completion evidence.
          </p>
        </div>
        <div className="p-3 bg-purple-50 text-purple-800 rounded-xl">
          <CheckSquare className="w-6 h-6" />
        </div>
      </div>

      {msg && <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg">{msg}</div>}

      {/* Undertakings Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-200">
          <h3 className="font-bold text-sm text-slate-900">Active Undertakings List ({undertakings.length})</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th className="p-3.5">Code</th>
                <th className="p-3.5">Title & Requirement Clause</th>
                <th className="p-3.5">Due Date</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">Evidence File</th>
                <th className="p-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={6} className="p-6 text-center text-slate-400">Loading undertakings...</td></tr>
              ) : undertakings.length === 0 ? (
                <tr><td colSpan={6} className="p-6 text-center text-slate-400">No active undertakings for your institution.</td></tr>
              ) : (
                undertakings.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                    <td className="p-3.5 font-bold font-mono text-purple-700">{u.undertaking_code}</td>
                    <td className="p-3.5">
                      <div className="font-semibold text-slate-900">{u.title}</div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">{u.requirement_clause}</div>
                      {u.correction_reason && (
                        <div className="mt-1 text-[11px] text-red-600 bg-red-50 p-1.5 rounded border border-red-200">
                          Correction Request: {u.correction_reason}
                        </div>
                      )}
                    </td>
                    <td className="p-3.5 font-mono text-slate-700">{new Date(u.due_date).toLocaleDateString()}</td>
                    <td className="p-3.5">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        u.status === 'ACCEPTED' ? 'bg-emerald-100 text-emerald-800' :
                        u.status === 'OVERDUE' ? 'bg-red-100 text-red-800 animate-pulse' :
                        u.status === 'CORRECTION_REQUESTED' ? 'bg-amber-100 text-amber-800' :
                        u.status === 'SUBMITTED' ? 'bg-blue-100 text-blue-800' :
                        'bg-slate-100 text-slate-800'
                      }`}>
                        {u.status}
                      </span>
                    </td>
                    <td className="p-3.5 font-mono text-slate-500">
                      {u.evidence_filename || 'Not Submitted'}
                    </td>
                    <td className="p-3.5 text-right">
                      {u.status !== 'ACCEPTED' && (
                        <button
                          onClick={() => setSelectedUt(u)}
                          className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-md font-semibold text-xs cursor-pointer inline-flex items-center gap-1"
                        >
                          <Upload className="w-3.5 h-3.5" /> Submit Evidence
                        </button>
                      )}
                      {u.status === 'ACCEPTED' && (
                        <span className="text-emerald-600 font-bold flex items-center justify-end gap-1">
                          <CheckCircle2 className="w-4 h-4" /> Verified
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Submission Modal */}
      {selectedUt && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Submit Compliance Evidence</h3>
            <p className="text-xs text-slate-500 mb-4">
              Undertaking: <strong className="text-slate-800">{selectedUt.undertaking_code} - {selectedUt.title}</strong>
            </p>

            <form onSubmit={handleEvidenceSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Evidence Description & Methodology</label>
                <textarea
                  rows={3}
                  value={evidenceDesc}
                  onChange={(e) => setEvidenceDesc(e.target.value)}
                  placeholder="Detail the work carried out, government clearance numbers, or statutory approvals..."
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Upload Supporting File (PDF, Certification)</label>
                <input
                  type="file"
                  accept=".pdf,.png,.jpeg,.jpg"
                  onChange={(e) => setEvidenceFile(e.target.files?.[0] || null)}
                  className="w-full text-xs p-1.5 border border-slate-300 rounded-lg bg-slate-50 cursor-pointer"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedUt(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  {isSubmitting ? 'Uploading...' : 'Confirm Submission'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
