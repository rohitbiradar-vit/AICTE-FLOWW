import React, { useEffect, useState } from 'react';
import { apiRequest, downloadFile } from '../../api/client';
import { CheckSquare, Clock, AlertTriangle, CheckCircle2, XCircle, Search, Download } from 'lucide-react';

export const ComplianceReview: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'UNDERTAKINGS' | 'EXPIRY_REGISTER'>('UNDERTAKINGS');
  const [undertakings, setUndertakings] = useState<any[]>([]);
  const [expiryDocs, setExpiryDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);
  const [downloadingEvidenceId, setDownloadingEvidenceId] = useState<number | null>(null);

  const handleDownloadDocument = async (docId: number, filename?: string) => {
    try {
      setDownloadingDocId(docId);
      await downloadFile(`/documents/${docId}/download`, filename);
    } catch (err: any) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setDownloadingDocId(null);
    }
  };

  const handleDownloadEvidence = async (undertakingId: number, filename?: string) => {
    try {
      setDownloadingEvidenceId(undertakingId);
      await downloadFile(`/compliance/undertakings/${undertakingId}/download-evidence`, filename);
    } catch (err: any) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setDownloadingEvidenceId(null);
    }
  };

  // Verification modal
  const [selectedUt, setSelectedUt] = useState<any | null>(null);
  const [decision, setDecision] = useState('ACCEPTED');
  const [notes, setNotes] = useState('');
  const [correctionReason, setCorrectionReason] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [uData, expData] = await Promise.all([
        apiRequest<any[]>('/compliance/undertakings'),
        apiRequest<any[]>('/compliance/document-expiry-register')
      ]);
      setUndertakings(uData || []);
      setExpiryDocs(expData || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUt) return;

    setIsVerifying(true);
    try {
      await apiRequest(`/compliance/undertakings/${selectedUt.id}/verify`, {
        method: 'POST',
        body: JSON.stringify({
          decision,
          notes,
          correction_reason: decision === 'CORRECTION_REQUESTED' ? correctionReason : undefined
        })
      });
      setSelectedUt(null);
      setNotes('');
      setCorrectionReason('');
      fetchData();
    } catch (err: any) {
      alert(`Verification error: ${err.message}`);
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap justify-between items-center gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-purple-700">Statutory Surveillance</span>
          <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">Compliance & Expiry Monitoring Bureau</h1>
          <p className="text-xs text-slate-500 mt-1">
            Audit submitted compliance undertakings and monitor expiring statutory licenses across colleges.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('UNDERTAKINGS')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeTab === 'UNDERTAKINGS' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Undertakings Queue ({undertakings.length})
          </button>
          <button
            onClick={() => setActiveTab('EXPIRY_REGISTER')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeTab === 'EXPIRY_REGISTER' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Document Expiry Register ({expiryDocs.length})
          </button>
        </div>
      </div>

      {/* Tab 1: Undertakings */}
      {activeTab === 'UNDERTAKINGS' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="p-3.5">Code</th>
                  <th className="p-3.5">Requirement & Title</th>
                  <th className="p-3.5">Due Date</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Evidence File</th>
                  <th className="p-3.5 text-right">Official Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {undertakings.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50">
                    <td className="p-3.5 font-mono font-bold text-purple-700">{u.undertaking_code}</td>
                    <td className="p-3.5">
                      <div className="font-semibold text-slate-900">{u.title}</div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">{u.requirement_clause}</div>
                    </td>
                    <td className="p-3.5 font-mono text-slate-700">{new Date(u.due_date).toLocaleDateString()}</td>
                    <td className="p-3.5">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        u.status === 'ACCEPTED' ? 'bg-emerald-100 text-emerald-800' :
                        u.status === 'OVERDUE' ? 'bg-rose-100 text-rose-800' :
                        u.status === 'SUBMITTED' ? 'bg-blue-100 text-blue-800' :
                        'bg-slate-100 text-slate-800'
                      }`}>
                        {u.status}
                      </span>
                    </td>
                    <td className="p-3.5 font-mono text-slate-600">
                      {u.evidence_filename ? (
                        <button
                          type="button"
                          onClick={() => handleDownloadEvidence(u.id, u.evidence_filename)}
                          disabled={downloadingEvidenceId === u.id}
                          className="text-purple-700 hover:text-purple-900 font-semibold underline inline-flex items-center gap-1 cursor-pointer disabled:opacity-50"
                        >
                          <Download className="w-3.5 h-3.5" />
                          {downloadingEvidenceId === u.id ? 'Downloading...' : u.evidence_filename}
                        </button>
                      ) : (
                        'Awaiting Upload'
                      )}
                    </td>
                    <td className="p-3.5 text-right">
                      <button
                        onClick={() => setSelectedUt(u)}
                        className="px-3 py-1 bg-purple-50 text-purple-700 hover:bg-purple-600 hover:text-white rounded-md font-semibold text-xs transition-colors cursor-pointer"
                      >
                        Verify Evidence
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Document Expiry Register */}
      {activeTab === 'EXPIRY_REGISTER' && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="p-3.5">Institution Name</th>
                  <th className="p-3.5">Document Title & Category</th>
                  <th className="p-3.5">Expiry Date</th>
                  <th className="p-3.5">Days Remaining</th>
                  <th className="p-3.5">Regulatory Status</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {expiryDocs.map((doc) => (
                  <tr key={doc.document_id} className="hover:bg-slate-50">
                    <td className="p-3.5 font-semibold text-slate-800">{doc.institution_name}</td>
                    <td className="p-3.5">
                      <div className="font-semibold text-slate-900">{doc.title}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{doc.document_type}</div>
                    </td>
                    <td className="p-3.5 font-mono text-slate-700">
                      {doc.expiry_date ? new Date(doc.expiry_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="p-3.5 font-mono font-bold">
                      <span className={doc.days_remaining < 0 ? 'text-red-600' : doc.days_remaining <= 30 ? 'text-amber-600' : 'text-slate-700'}>
                        {doc.days_remaining < 0 ? `${Math.abs(doc.days_remaining)} days ago` : `${doc.days_remaining} days`}
                      </span>
                    </td>
                    <td className="p-3.5">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        doc.expiry_status === 'EXPIRED' ? 'bg-red-100 text-red-800' :
                        doc.expiry_status === 'CRITICAL_RENEWAL_REQUIRED' ? 'bg-amber-100 text-amber-800' :
                        doc.expiry_status === 'UPCOMING_EXPIRY' ? 'bg-purple-100 text-purple-800' :
                        'bg-emerald-100 text-emerald-800'
                      }`}>
                        {doc.expiry_status}
                      </span>
                    </td>
                    <td className="p-3.5 text-right">
                      <button
                        type="button"
                        onClick={() => handleDownloadDocument(doc.document_id, doc.title)}
                        disabled={downloadingDocId === doc.document_id}
                        className="text-xs font-semibold text-blue-600 hover:underline cursor-pointer disabled:opacity-50"
                      >
                        {downloadingDocId === doc.document_id ? 'Downloading...' : 'Inspect Certificate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Verify Undertaking Modal */}
      {selectedUt && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Verify Compliance Evidence</h3>
            <p className="text-xs text-slate-500 mb-4">
              Undertaking: <strong className="text-slate-800">{selectedUt.undertaking_code} - {selectedUt.title}</strong>
            </p>

            <form onSubmit={handleVerifySubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Official Decision</label>
                <select
                  value={decision}
                  onChange={(e) => setDecision(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                >
                  <option value="ACCEPTED">ACCEPTED (Satisfactory Evidence)</option>
                  <option value="CORRECTION_REQUESTED">CORRECTION_REQUESTED (Incomplete Evidence)</option>
                  <option value="REJECTED">REJECTED (Non-compliant)</option>
                </select>
              </div>

              {decision === 'CORRECTION_REQUESTED' && (
                <div>
                  <label className="block text-xs font-semibold text-red-700 mb-1">Mandatory Correction Reason</label>
                  <textarea
                    rows={2}
                    value={correctionReason}
                    onChange={(e) => setCorrectionReason(e.target.value)}
                    placeholder="Detail specific omissions or corrections required..."
                    className="w-full text-xs p-2.5 border border-red-300 rounded-lg bg-red-50"
                    required
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Verification Observations & Notes</label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Record officer audit findings..."
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
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
                  disabled={isVerifying}
                  className="px-4 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  {isVerifying ? 'Saving...' : 'Record Verification'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
