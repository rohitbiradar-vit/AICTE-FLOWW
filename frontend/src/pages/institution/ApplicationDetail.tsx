import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiRequest, downloadFile } from '../../api/client';
import { DualClockVisualizer } from '../../components/DualClockVisualizer';
import { ScrutinyReportCard } from '../../components/ScrutinyReportCard';
import {
  ArrowLeft, Send, AlertTriangle, FileText, UploadCloud, CheckCircle,
  History, Clock, Building, ShieldCheck
} from 'lucide-react';

export const ApplicationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [app, setApp] = useState<any>(null);
  const [clockData, setClockData] = useState<any>(null);
  const [scrutinyReport, setScrutinyReport] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Clarification form state
  const [clarificationResponse, setClarificationResponse] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);

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

  const fetchApplicationDetails = async () => {
    try {
      const [appData, clock, report, hist, docs] = await Promise.all([
        apiRequest(`/applications/${id}`),
        apiRequest(`/applications/${id}/clock-summary`),
        apiRequest(`/scrutiny/applications/${id}/latest`).catch(() => null),
        apiRequest(`/applications/${id}/history`).catch(() => []),
        apiRequest(`/documents?application_id=${id}`).catch(() => [])
      ]);
      setApp(appData);
      setClockData(clock);
      setScrutinyReport(report);
      setHistory(hist);
      setDocuments(docs);
    } catch (err: any) {
      setError(err.message || 'Failed to load application details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplicationDetails();
  }, [id]);

  const handleSubmitDraft = async () => {
    setIsSubmitting(true);
    try {
      await apiRequest(`/applications/${id}/transition`, {
        method: 'POST',
        body: JSON.stringify({
          target_stage_key: 'SUBMITTED',
          reason: 'Application dossier finalized and submitted by institution.'
        })
      });
      fetchApplicationDetails();
    } catch (err: any) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResubmitClarification = async () => {
    if (!clarificationResponse.trim()) {
      alert('Please provide detailed clarification explanations before resubmitting.');
      return;
    }
    setIsSubmitting(true);
    try {
      await apiRequest(`/applications/${id}/transition`, {
        method: 'POST',
        body: JSON.stringify({
          target_stage_key: 'RESUBMITTED',
          reason: clarificationResponse
        })
      });
      setClarificationResponse('');
      fetchApplicationDetails();
    } catch (err: any) {
      alert(`Resubmission error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-500">Loading application details...</div>;
  }

  if (error || !app) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs">
          {error || 'Application not found.'}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link to="/institution/applications" className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1.5">
          <ArrowLeft className="w-4 h-4" /> Back to Applications
        </Link>
      </div>

      {/* Application Title Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap justify-between items-start gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-slate-900 font-mono">{app.application_number}</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-900 border border-blue-200">
              {app.current_stage_key.replace(/_/g, ' ')}
            </span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
              app.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' :
              app.status === 'REJECTED' ? 'bg-rose-100 text-rose-800' :
              'bg-amber-100 text-amber-800'
            }`}>
              {app.status}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {app.application_type.replace(/_/g, ' ')} • Academic Session: {app.academic_year} • Institution: {app.institution_name}
          </p>
        </div>

        {/* Action button if Draft */}
        {app.current_stage_key === 'DRAFT' && (
          <button
            onClick={handleSubmitDraft}
            disabled={isSubmitting}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-md cursor-pointer"
          >
            <Send className="w-4 h-4" />
            <span>{isSubmitting ? 'Submitting...' : 'Submit to AICTE Bureau'}</span>
          </button>
        )}
      </div>

      {/* CLARIFICATION REQUIRED CALLOUT BOX */}
      {app.current_stage_key === 'CLARIFICATION_REQUIRED' && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-2xl p-5 shadow-xs space-y-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-bold text-sm text-amber-950">Clarification Requested by AICTE Scrutiny Bureau</h3>
              <p className="text-xs text-amber-800 mt-1 font-medium bg-amber-100/70 p-3 rounded-lg border border-amber-200">
                "{app.clarification_notes || 'Please review highlighted document inconsistencies and resubmit evidence.'}"
              </p>
            </div>
          </div>

          <div className="pt-2">
            <label className="block text-xs font-bold text-amber-950 mb-1">
              Institutional Clarification Response & Resubmission Statement
            </label>
            <textarea
              rows={3}
              value={clarificationResponse}
              onChange={(e) => setClarificationResponse(e.target.value)}
              placeholder="Detail your corrections and explanations here. Institutional clock will stop upon resubmission."
              className="w-full text-xs p-3 bg-white border border-amber-300 rounded-lg text-slate-800"
            />
            <div className="flex justify-end mt-2">
              <button
                onClick={handleResubmitClarification}
                disabled={isSubmitting}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-md cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{isSubmitting ? 'Resubmitting...' : 'Resubmit Clarification Dossier'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DUAL-CLOCK VISUALIZER */}
      {clockData && (
        <DualClockVisualizer clockData={clockData} />
      )}

      {/* AI SCRUTINY REPORT & PRIORITY SCORE */}
      {scrutinyReport && (
        <ScrutinyReportCard report={scrutinyReport} canReview={false} />
      )}

      {/* Supporting Documents Section */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="font-bold text-sm text-slate-900">Application Supporting Documents ({documents.length})</h3>
            <p className="text-xs text-slate-500">Privately stored statutory documents subjected to automated scrutiny.</p>
          </div>
          <Link
            to="/institution/documents"
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
          >
            <UploadCloud className="w-4 h-4" /> Manage / Upload More Documents
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
              <tr>
                <th className="p-3">Document Title</th>
                <th className="p-3">Type</th>
                <th className="p-3">Version</th>
                <th className="p-3">Expiry Date</th>
                <th className="p-3">Verification Status</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-4 text-center text-slate-400">
                    No documents linked to this application yet.
                  </td>
                </tr>
              ) : (
                documents.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50">
                    <td className="p-3 font-semibold text-slate-800">{d.title}</td>
                    <td className="p-3 text-slate-600 font-mono">{d.document_type}</td>
                    <td className="p-3 font-mono">v{d.version}</td>
                    <td className="p-3 font-mono">
                      {d.expiry_date ? new Date(d.expiry_date).toLocaleDateString() : 'Permanent'}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        d.verification_status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800' :
                        d.verification_status === 'REJECTED' ? 'bg-rose-100 text-rose-800' :
                        'bg-slate-100 text-slate-800'
                      }`}>
                        {d.verification_status}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleDownloadDocument(d.id, d.original_filename)}
                        disabled={downloadingDocId === d.id}
                        className="text-xs font-semibold text-blue-600 hover:underline cursor-pointer disabled:opacity-50"
                      >
                        {downloadingDocId === d.id ? 'Downloading...' : 'Download PDF'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Workflow Transition History Audit Trail */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
        <h3 className="font-bold text-sm text-slate-900 mb-1 flex items-center gap-2">
          <History className="w-4 h-4 text-blue-600" />
          Statutory Audit Trail & Workflow Transition Log
        </h3>
        <p className="text-xs text-slate-500 mb-4">Complete chronological history of stage entries, exits, and administrative decisions.</p>

        <div className="space-y-3">
          {history.length === 0 ? (
            <div className="text-xs text-slate-400 italic">No stage transitions recorded yet.</div>
          ) : (
            history.map((h) => (
              <div key={h.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs flex justify-between items-start gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-800">{h.transition_name || 'Stage Transition'}</span>
                    <span className="font-mono text-[11px] bg-slate-200 px-2 py-0.5 rounded text-slate-700">
                      {h.from_stage} → {h.to_stage}
                    </span>
                  </div>
                  {h.reason && <p className="text-slate-600 mt-1 italic">"{h.reason}"</p>}
                  <div className="text-[11px] text-slate-400 mt-1">
                    Transitioned by: <strong className="text-slate-600">{h.transitioned_by_name}</strong>
                  </div>
                </div>
                <div className="font-mono text-slate-500 text-[11px] shrink-0">
                  {new Date(h.created_at).toLocaleString()}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
