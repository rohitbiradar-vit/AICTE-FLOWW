import React, { useState } from 'react';
import {
  ShieldAlert, AlertTriangle, CheckCircle, FileText,
  AlertCircle, ChevronDown, ChevronUp, UserCheck, HelpCircle
} from 'lucide-react';

interface ScrutinyReportProps {
  report: {
    id: number;
    application_id: number;
    report_version: number;
    priority_score: number;
    priority_band: 'STANDARD' | 'ENHANCED' | 'HIGH';
    score_formula_breakdown: {
      final_score: number;
      band: string;
      formula: string;
      factor_contributions: Array<{
        factor: string;
        points: number;
        explanation: string;
      }>;
      governance_rule: string;
    };
    document_inventory: Array<{
      document_type: string;
      title: string;
      file_size_kb: number;
      verification_status: string;
      overall_confidence: number;
    }>;
    extracted_summary: Record<string, any>;
    missing_evidence: Array<{
      document_type: string;
      issue: string;
      severity: string;
    }>;
    inconsistencies: Array<{
      field: string;
      declared_in_application: string;
      extracted_from_document: string;
      issue: string;
      source_reference: string;
    }>;
    expiry_findings: Array<{
      title: string;
      expiry_date: string;
      issue: string;
      severity: string;
    }>;
    low_confidence_extractions: Array<{
      title: string;
      confidence: number;
      issue: string;
      source_reference: string;
    }>;
    findings_requiring_human_review: Array<any>;
    rules_checked: Array<{ rule: string; status: string }>;
    suggested_actions: string[];
    reviewer_decision: string;
    reviewer_notes?: string;
  };
  onReviewSubmit?: (decision: string, notes: string) => void;
  canReview?: boolean;
}

export const ScrutinyReportCard: React.FC<ScrutinyReportProps> = ({
  report,
  onReviewSubmit,
  canReview = false
}) => {
  const [showFormula, setShowFormula] = useState(false);
  const [reviewDecision, setReviewDecision] = useState('AGREED');
  const [reviewNotes, setReviewNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getBandBadge = (band: string) => {
    switch (band) {
      case 'HIGH':
        return (
          <div className="flex items-center gap-2 px-3 py-1 bg-red-100 border border-red-300 text-red-800 rounded-lg text-xs font-bold">
            <ShieldAlert className="w-4 h-4 text-red-600" />
            HIGH SCRUTINY PRIORITY (Score: {report.priority_score}/100)
          </div>
        );
      case 'ENHANCED':
        return (
          <div className="flex items-center gap-2 px-3 py-1 bg-amber-100 border border-amber-300 text-amber-800 rounded-lg text-xs font-bold">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            ENHANCED SCRUTINY PRIORITY (Score: {report.priority_score}/100)
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-100 border border-emerald-300 text-emerald-800 rounded-lg text-xs font-bold">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            STANDARD SCRUTINY PRIORITY (Score: {report.priority_score}/100)
          </div>
        );
    }
  };

  const handleReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!onReviewSubmit) return;
    setIsSubmitting(true);
    try {
      await onReviewSubmit(reviewDecision, reviewNotes);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden space-y-4">
      {/* Header Banner */}
      <div className="p-4 bg-slate-900 text-white flex flex-wrap justify-between items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-base">Secure AI Scrutiny Intelligence Report</h3>
            <span className="text-xs bg-blue-900 text-blue-200 px-2 py-0.5 rounded font-mono">
              Version {report.report_version}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic rule extraction & explainable scrutiny triage engine under AICTE Approval Process.
          </p>
        </div>
        <div>{getBandBadge(report.priority_band)}</div>
      </div>

      <div className="p-5 space-y-6">
        {/* Priority Score & Explainable Formula breakdown */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
          <div className="flex flex-wrap justify-between items-center gap-2">
            <div>
              <span className="text-xs font-semibold text-slate-500 uppercase">Scrutiny Attention Meter</span>
              <div className="flex items-baseline gap-2 mt-0.5">
                <span className="text-3xl font-extrabold text-slate-900 font-mono">{report.priority_score}</span>
                <span className="text-xs text-slate-500 font-mono">/ 100 max scrutiny score</span>
              </div>
            </div>
            <button
              onClick={() => setShowFormula(!showFormula)}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 cursor-pointer"
            >
              <HelpCircle className="w-4 h-4" />
              {showFormula ? 'Hide Formula Breakdown' : 'Explain Why This Score Was Assigned'}
              {showFormula ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden mt-3">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                report.priority_score >= 75 ? 'bg-red-500' : report.priority_score >= 25 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.max(5, report.priority_score)}%` }}
            />
          </div>

          {/* Governance Notice */}
          <p className="text-xs text-slate-500 mt-3 italic">
            * Governance Notice: Scrutiny Priority Score measures review complexity. A low score does not bypass scrutiny, nor does a high score reject an application.
          </p>

          {/* Expanded Factor Breakdown */}
          {showFormula && (
            <div className="mt-4 pt-4 border-t border-slate-200 space-y-2">
              <div className="text-xs font-bold text-slate-700 mb-2">Documented Factor Scoring Breakdown:</div>
              {report.score_formula_breakdown?.factor_contributions?.map((f, i) => (
                <div key={i} className="flex justify-between items-center text-xs p-2 bg-white rounded border border-slate-200">
                  <div>
                    <span className="font-semibold text-slate-800">{f.factor}: </span>
                    <span className="text-slate-600">{f.explanation}</span>
                  </div>
                  <span className="font-mono font-bold text-slate-900 shrink-0 ml-2">+{f.points} pts</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Missing Evidence Section */}
        {report.missing_evidence && report.missing_evidence.length > 0 && (
          <div className="border border-red-200 bg-red-50/50 rounded-xl p-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-red-800 flex items-center gap-1.5 mb-2">
              <AlertCircle className="w-4 h-4 text-red-600" />
              Missing Required Mandatory Evidence ({report.missing_evidence.length})
            </h4>
            <div className="space-y-2">
              {report.missing_evidence.map((m, idx) => (
                <div key={idx} className="text-xs bg-white p-2.5 rounded border border-red-200 text-slate-800 flex justify-between items-center">
                  <div>
                    <span className="font-bold text-red-900">{m.document_type.replace(/_/g, ' ')}: </span>
                    <span>{m.issue}</span>
                  </div>
                  <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded font-bold text-[10px] uppercase">
                    {m.severity}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cross-Document Inconsistencies */}
        {report.inconsistencies && report.inconsistencies.length > 0 && (
          <div className="border border-amber-200 bg-amber-50/50 rounded-xl p-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800 flex items-center gap-1.5 mb-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              Cross-Document Inconsistencies Detected ({report.inconsistencies.length})
            </h4>
            <div className="space-y-2">
              {report.inconsistencies.map((inc, idx) => (
                <div key={idx} className="text-xs bg-white p-3 rounded border border-amber-200 space-y-1">
                  <div className="flex justify-between items-start">
                    <span className="font-bold text-slate-800">Field: {inc.field}</span>
                    <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                      Citation: {inc.source_reference}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px] p-2 bg-slate-50 rounded">
                    <div>
                      <span className="text-slate-500">Declared in Application:</span>
                      <p className="font-semibold text-slate-800">{inc.declared_in_application}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Extracted from Certificate:</span>
                      <p className="font-semibold text-amber-900">{inc.extracted_from_document}</p>
                    </div>
                  </div>
                  <p className="text-slate-600 pt-1 text-[11px]">{inc.issue}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Expiry Findings */}
        {report.expiry_findings && report.expiry_findings.length > 0 && (
          <div className="border border-purple-200 bg-purple-50/40 rounded-xl p-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-purple-800 flex items-center gap-1.5 mb-2">
              <FileText className="w-4 h-4 text-purple-600" />
              Document Expiry & Renewal Alerts ({report.expiry_findings.length})
            </h4>
            <div className="space-y-2">
              {report.expiry_findings.map((exp, idx) => (
                <div key={idx} className="text-xs bg-white p-2.5 rounded border border-purple-200 flex justify-between items-center">
                  <div>
                    <span className="font-semibold text-slate-800">{exp.title}: </span>
                    <span className="text-slate-600">{exp.issue}</span>
                  </div>
                  <span className="font-mono text-xs font-bold text-purple-900 ml-2 shrink-0">
                    Expiry: {exp.expiry_date}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Suggested Administrative Actions */}
        {report.suggested_actions && report.suggested_actions.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-xs">
            <h4 className="font-bold text-blue-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-blue-700" />
              Suggested Administrative Actions for Scrutiny Officer
            </h4>
            <ul className="list-disc list-inside space-y-1 text-slate-700">
              {report.suggested_actions.map((act, i) => (
                <li key={i}>{act}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Official Review / Override Section */}
        {canReview && (
          <div className="border-t border-slate-200 pt-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3">
              Official Regulatory Review & Score Confirmation
            </h4>
            <form onSubmit={handleReview} className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center gap-1.5 text-xs font-medium cursor-pointer">
                  <input
                    type="radio"
                    name="decision"
                    value="AGREED"
                    checked={reviewDecision === 'AGREED'}
                    onChange={(e) => setReviewDecision(e.target.value)}
                  />
                  <span>Confirm AI Findings & Score</span>
                </label>
                <label className="flex items-center gap-1.5 text-xs font-medium cursor-pointer">
                  <input
                    type="radio"
                    name="decision"
                    value="OVERRIDDEN"
                    checked={reviewDecision === 'OVERRIDDEN'}
                    onChange={(e) => setReviewDecision(e.target.value)}
                  />
                  <span>Override / Modify AI Findings</span>
                </label>
                <label className="flex items-center gap-1.5 text-xs font-medium cursor-pointer">
                  <input
                    type="radio"
                    name="decision"
                    value="RETURN_FOR_CLARIFICATION"
                    checked={reviewDecision === 'RETURN_FOR_CLARIFICATION'}
                    onChange={(e) => setReviewDecision(e.target.value)}
                  />
                  <span>Return to Institution for Clarification</span>
                </label>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Scrutiny Officer Review Observations
                </label>
                <textarea
                  rows={2}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Record verification notes, justification for override, or required clarification points..."
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-md bg-white"
                />
              </div>

              <div className="flex justify-between items-center pt-1">
                <div className="text-[11px] text-slate-500">
                  Current Status: <strong className="text-slate-800">{report.reviewer_decision}</strong>
                  {report.reviewer_notes && <span> — "{report.reviewer_notes}"</span>}
                </div>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold cursor-pointer"
                >
                  {isSubmitting ? 'Recording...' : 'Record Regulatory Review'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};
