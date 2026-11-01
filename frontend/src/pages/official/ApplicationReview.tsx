import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiRequest, downloadFile } from '../../api/client';
import { DualClockVisualizer } from '../../components/DualClockVisualizer';
import { ScrutinyReportCard } from '../../components/ScrutinyReportCard';
import {
  ArrowLeft, Send, CheckCircle2, AlertTriangle, FileText, Download,
  Layers, UserCheck, Shield, ChevronRight
} from 'lucide-react';

export const ApplicationReview: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [app, setApp] = useState<any>(null);
  const [clockData, setClockData] = useState<any>(null);
  const [scrutinyReport, setScrutinyReport] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Transition form
  const [targetStage, setTargetStage] = useState('');
  const [transitionReason, setTransitionReason] = useState('');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionMsg, setTransitionMsg] = useState('');
  const [transitionErr, setTransitionErr] = useState('');
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);

  const handleDownload = async (docId: number, filename?: string) => {
    try {
      setDownloadingDocId(docId);
      await downloadFile(`/documents/${docId}/download`, filename);
    } catch (err: any) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setDownloadingDocId(null);
    }
  };

  const fetchAll = async () => {
    try {
      const [appData, clock, report, docs] = await Promise.all([
        apiRequest(`/applications/${id}`),
        apiRequest(`/applications/${id}/clock-summary`),
        apiRequest(`/scrutiny/applications/${id}/latest`).catch(() => null),
        apiRequest(`/documents?application_id=${id}`).catch(() => [])
      ]);
      setApp(appData);
      setClockData(clock);
      setScrutinyReport(report);
      setDocuments(docs);

      // Default next stage suggestions
      if (appData.current_stage_key === 'SUBMITTED') {
        setTargetStage('INITIAL_SCRUTINY');
      } else if (appData.current_stage_key === 'INITIAL_SCRUTINY') {
        setTargetStage('EVC_SCHEDULED');
      } else if (appData.current_stage_key === 'RESUBMITTED') {
        setTargetStage('FURTHER_REVIEW');
      } else if (appData.current_stage_key === 'FURTHER_REVIEW') {
        setTargetStage('EVC_SCHEDULED');
      } else if (appData.current_stage_key === 'EVC_COMPLETED') {
        setTargetStage('COMMITTEE_REVIEW');
      } else if (appData.current_stage_key === 'COMMITTEE_REVIEW') {
        setTargetStage('FINAL_APPROVAL');
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, [id]);

  const handleTransitionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetStage) return;

    setIsTransitioning(true);
    setTransitionErr('');
    setTransitionMsg('');

    try {
      await apiRequest(`/applications/${id}/transition`, {
        method: 'POST',
        body: JSON.stringify({
          target_stage_key: targetStage,
          reason: transitionReason
        })
      });
      setTransitionMsg(`Application successfully transitioned to ${targetStage}!`);
      setTransitionReason('');
      fetchAll();
    } catch (err: any) {
      setTransitionErr(err.message || 'Transition rejected by workflow engine.');
    } finally {
      setIsTransitioning(false);
    }
  };

  const handleOfficialReview = async (decision: string, notes: string) => {
    if (!scrutinyReport) return;
    await apiRequest(`/scrutiny/reports/${scrutinyReport.id}/review`, {
      method: 'POST',
      body: JSON.stringify({ decision, notes })
    });
    fetchAll();
  };

  const handleDocumentVerify = async (docId: number, status: string) => {
    await apiRequest(`/documents/${docId}/verify`, {
      method: 'POST',
      body: JSON.stringify({
        verification_status: status,
        verification_notes: `Marked as ${status} by official reviewer.`
      })
    });
    fetchAll();
  };

  const handleClockPause = async (reason: string, clause?: string) => {
    await apiRequest(`/applications/${id}/clock/pause`, {
      method: 'POST',
      body: JSON.stringify({ reason, authorized_clause: clause })
    });
    fetchAll();
  };

  const handleClockResume = async () => {
    await apiRequest(`/applications/${id}/clock/resume`, {
      method: 'POST'
    });
    fetchAll();
  };

  if (loading) return <div className="p-8 text-center text-xs text-slate-500">Loading dossier review...</div>;
  if (!app) return <div className="p-8 text-center text-xs text-slate-500">Application not found.</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link to="/official/work-queue" className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1.5">
          <ArrowLeft className="w-4 h-4" /> Back to Official Work Queue
        </Link>
      </div>

      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap justify-between items-start gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-slate-900 font-mono">{app.application_number}</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-900 border border-blue-200">
              {app.current_stage_key.replace(/_/g, ' ')}
            </span>
          </div>
          <p className="text-xs text-slate-600 mt-1">
            <strong>{app.institution_name}</strong> • {app.application_type.replace(/_/g, ' ')} • Session: {app.academic_year}
          </p>
        </div>

        <div className="text-right text-xs">
          <div className="text-slate-500">SLA Deadline:</div>
          <div className="font-mono font-bold text-slate-900">
            {app.current_deadline ? new Date(app.current_deadline).toLocaleString() : 'N/A'}
          </div>
        </div>
      </div>

      {/* DUAL-CLOCK VISUALIZER WITH PAUSE / RESUME CONTROLS */}
      {clockData && (
        <DualClockVisualizer
          clockData={clockData}
          onPause={handleClockPause}
          onResume={handleClockResume}
          canManageClock={true}
        />
      )}

      {/* REGULATORY STAGE TRANSITION ACTION BOX */}
      <div className="bg-white rounded-2xl border-2 border-blue-600/30 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
          <Layers className="w-5 h-5 text-blue-600" />
          <div>
            <h3 className="font-bold text-sm text-slate-900">Regulatory Stage Transition & Workflow Action</h3>
            <p className="text-xs text-slate-500">Authorized officials can record formal stage decisions and transition the dossier.</p>
          </div>
        </div>

        {transitionErr && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">{transitionErr}</div>
        )}
        {transitionMsg && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg">{transitionMsg}</div>
        )}

        <form onSubmit={handleTransitionSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Select Permitted Next Stage</label>
              <select
                value={targetStage}
                onChange={(e) => setTargetStage(e.target.value)}
                className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-slate-50 font-semibold"
                required
              >
                <option value="">-- Choose Target Stage --</option>
                <option value="INITIAL_SCRUTINY">INITIAL_SCRUTINY (Start Official Scrutiny)</option>
                <option value="CLARIFICATION_REQUIRED">CLARIFICATION_REQUIRED (Return to Institution)</option>
                <option value="FURTHER_REVIEW">FURTHER_REVIEW (Resume Scrutiny)</option>
                <option value="EVC_SCHEDULED">EVC_SCHEDULED (Refer to Expert Visiting Committee)</option>
                <option value="EVC_COMPLETED">EVC_COMPLETED (Complete Inspection Report)</option>
                <option value="COMMITTEE_REVIEW">COMMITTEE_REVIEW (Forward to Bureau Committee)</option>
                <option value="FINAL_APPROVAL">FINAL_APPROVAL (Grant AICTE Approval)</option>
                <option value="REJECTED">REJECTED (Statutory Rejection)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Reason / Detailed Regulatory Observations
                {targetStage === 'CLARIFICATION_REQUIRED' && <span className="text-red-600 font-bold"> (MANDATORY)</span>}
              </label>
              <input
                type="text"
                value={transitionReason}
                onChange={(e) => setTransitionReason(e.target.value)}
                placeholder="Required for returning for clarification or rejection..."
                className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isTransitioning}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-md cursor-pointer flex items-center gap-1.5"
            >
              <Send className="w-4 h-4" />
              <span>{isTransitioning ? 'Executing...' : 'Execute Authorized Stage Transition'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* AI SCRUTINY INTELLIGENCE REPORT WITH REVIEW CAPABILITY */}
      {scrutinyReport && (
        <ScrutinyReportCard
          report={scrutinyReport}
          onReviewSubmit={handleOfficialReview}
          canReview={true}
        />
      )}

      {/* DOCUMENT SCRUTINY & VERIFICATION TABLE */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
        <h3 className="font-bold text-sm text-slate-900 mb-1">Uploaded Statutory Documents & Officer Verification</h3>
        <p className="text-xs text-slate-500 mb-4">Confirm extracted evidence against source certificates.</p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th className="p-3">Title & Original File</th>
                <th className="p-3">Category</th>
                <th className="p-3">Version</th>
                <th className="p-3">Status</th>
                <th className="p-3">Source Download</th>
                <th className="p-3 text-right">Verification Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {documents.map((d) => (
                <tr key={d.id} className="hover:bg-slate-50">
                  <td className="p-3 font-semibold text-slate-900">
                    <div>{d.title}</div>
                    <div className="text-[10px] text-slate-400 font-mono">{d.original_filename}</div>
                  </td>
                  <td className="p-3 font-mono text-slate-600">{d.document_type}</td>
                  <td className="p-3 font-mono font-bold text-blue-700">v{d.version}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      d.verification_status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800' :
                      d.verification_status === 'REJECTED' ? 'bg-rose-100 text-rose-800' :
                      'bg-slate-100 text-slate-800'
                    }`}>
                      {d.verification_status}
                    </span>
                  </td>
                  <td className="p-3">
                    <button
                      type="button"
                      onClick={() => handleDownload(d.id, d.original_filename)}
                      disabled={downloadingDocId === d.id}
                      className="text-xs font-semibold text-blue-600 hover:underline inline-flex items-center gap-1 cursor-pointer disabled:opacity-50"
                    >
                      <Download className="w-3.5 h-3.5" /> {downloadingDocId === d.id ? 'Downloading...' : 'View PDF'}
                    </button>
                  </td>
                  <td className="p-3 text-right space-x-1.5">
                    <button
                      onClick={() => handleDocumentVerify(d.id, 'VERIFIED')}
                      className="px-2.5 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-600 hover:text-white rounded text-[11px] font-bold cursor-pointer"
                    >
                      Verify
                    </button>
                    <button
                      onClick={() => handleDocumentVerify(d.id, 'REJECTED')}
                      className="px-2.5 py-1 bg-rose-50 text-rose-700 hover:bg-rose-600 hover:text-white rounded text-[11px] font-bold cursor-pointer"
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
