import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { GitBranch, Layers, ShieldCheck, Clock, CheckCircle } from 'lucide-react';

export const WorkflowConfig: React.FC = () => {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<any[]>('/admin/workflow/definitions')
      .then((data) => setWorkflows(data || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-center text-xs text-slate-500">Loading workflow engine configuration...</div>;

  const activeWf = workflows[0];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex justify-between items-center">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-purple-700">Configurable State Machine</span>
          <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">Workflow Definition & Transition Rules</h1>
          <p className="text-xs text-slate-500 mt-1">
            Engine version: <strong className="font-mono text-slate-800">{activeWf?.version || '1.0'}</strong> • Server-enforced permissions and prerequisites.
          </p>
        </div>
        <div className="p-3 bg-purple-50 text-purple-800 rounded-xl">
          <GitBranch className="w-6 h-6" />
        </div>
      </div>

      {activeWf && (
        <div className="space-y-6">
          {/* Stages Table */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-slate-200">
              <h3 className="font-bold text-sm text-slate-900">Configured Regulatory Stages ({activeWf.stages?.length})</h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="p-3">Order</th>
                    <th className="p-3">Stage Key & Name</th>
                    <th className="p-3">Clock Attribution</th>
                    <th className="p-3">SLA Threshold</th>
                    <th className="p-3">Authorized Roles</th>
                    <th className="p-3">Terminal State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activeWf.stages?.map((s: any) => (
                    <tr key={s.stage_key} className="hover:bg-slate-50">
                      <td className="p-3 font-mono font-bold text-slate-500">{s.stage_order}</td>
                      <td className="p-3 font-semibold text-slate-900">
                        <div>{s.stage_name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{s.stage_key}</div>
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          s.clock_attribution === 'INSTITUTION' ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'
                        }`}>
                          {s.clock_attribution}
                        </span>
                      </td>
                      <td className="p-3 font-mono text-slate-700">{s.sla_hours} hours</td>
                      <td className="p-3">
                        <div className="flex flex-wrap gap-1">
                          {s.allowed_roles?.map((r: string, idx: number) => (
                            <span key={idx} className="px-1.5 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-mono">
                              {r}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="p-3">
                        {s.is_terminal ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-white">Terminal</span>
                        ) : (
                          <span className="text-slate-400">No</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Transitions Table */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-slate-200">
              <h3 className="font-bold text-sm text-slate-900">Configured State Transitions ({activeWf.transitions?.length})</h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="p-3">Transition Name</th>
                    <th className="p-3">From Stage → To Stage</th>
                    <th className="p-3">Reason Required</th>
                    <th className="p-3">Permitted Trigger Roles</th>
                    <th className="p-3">Prerequisites Checked</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activeWf.transitions?.map((t: any) => (
                    <tr key={t.id} className="hover:bg-slate-50">
                      <td className="p-3 font-bold text-slate-800">{t.transition_name}</td>
                      <td className="p-3 font-mono text-[11px] text-blue-700 font-semibold">
                        {t.from_stage_key} → {t.to_stage_key}
                      </td>
                      <td className="p-3">
                        {t.requires_reason ? (
                          <span className="text-red-600 font-bold">Mandatory</span>
                        ) : (
                          <span className="text-slate-400">Optional</span>
                        )}
                      </td>
                      <td className="p-3">
                        <div className="flex flex-wrap gap-1">
                          {t.allowed_roles?.map((r: string, idx: number) => (
                            <span key={idx} className="px-1.5 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-mono">
                              {r}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="p-3 text-[11px] font-mono text-slate-600">
                        {Object.keys(t.prerequisites || {}).length > 0 ? JSON.stringify(t.prerequisites) : 'None'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
