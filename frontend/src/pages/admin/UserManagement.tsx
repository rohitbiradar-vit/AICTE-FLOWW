import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { Users, Plus, ShieldCheck, Mail, Building2 } from 'lucide-react';

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [institutions, setInstitutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // New user form modal
  const [showModal, setShowModal] = useState(false);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('DemoPass123!');
  const [role, setRole] = useState('SCRUTINY_OFFICER');
  const [institutionId, setInstitutionId] = useState('');
  const [region, setRegion] = useState('Northern');
  const [formErr, setFormErr] = useState('');

  const fetchUsersAndInstitutions = async () => {
    setLoading(true);
    try {
      const [uData, iData] = await Promise.all([
        apiRequest<any[]>('/admin/users'),
        apiRequest<any[]>('/admin/institutions')
      ]);
      setUsers(uData || []);
      setInstitutions(iData || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsersAndInstitutions();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErr('');

    try {
      await apiRequest('/admin/users', {
        method: 'POST',
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          role,
          region,
          institution_id: role === 'INSTITUTION' && institutionId ? parseInt(institutionId) : null
        })
      });
      setShowModal(false);
      setFullName('');
      setEmail('');
      fetchUsersAndInstitutions();
    } catch (err: any) {
      setFormErr(err.message || 'Failed to create user.');
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap justify-between items-center gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-blue-700">Access Control & Governance</span>
          <h1 className="text-xl font-extrabold text-slate-900 mt-0.5">User & Role Provisioning</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage granular official roles and verified institutional user credentials.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center gap-2 cursor-pointer"
        >
          <Plus className="w-4 h-4" /> Provision New User
        </button>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th className="p-3.5">User Name</th>
                <th className="p-3.5">Email Address</th>
                <th className="p-3.5">Role</th>
                <th className="p-3.5">Region</th>
                <th className="p-3.5">Linked Institution</th>
                <th className="p-3.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => {
                const linkedInst = institutions.find(i => i.id === u.institution_id);
                return (
                  <tr key={u.id} className="hover:bg-slate-50">
                    <td className="p-3.5 font-bold text-slate-900">{u.full_name}</td>
                    <td className="p-3.5 font-mono text-slate-600">{u.email}</td>
                    <td className="p-3.5">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        u.role === 'ADMIN' ? 'bg-purple-100 text-purple-800' :
                        u.role === 'INSTITUTION' ? 'bg-amber-100 text-amber-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="p-3.5 text-slate-600">{u.region || 'Head Office'}</td>
                    <td className="p-3.5 text-slate-700 font-medium">{linkedInst ? linkedInst.name : 'N/A (Official/Admin)'}</td>
                    <td className="p-3.5">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                        Active
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Provisioning Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Provision Platform User</h3>
            <p className="text-xs text-slate-500 mb-4">Assign granular role-based permissions.</p>

            {formErr && <div className="mb-3 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">{formErr}</div>}

            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Dr. Ramesh Kumar"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@aicte.gov.in"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Role</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                  >
                    <option value="SCRUTINY_OFFICER">Scrutiny Officer</option>
                    <option value="EVC_COORDINATOR">EVC Coordinator</option>
                    <option value="DOCUMENT_VERIFIER">Document Verifier</option>
                    <option value="COMPLIANCE_OFFICER">Compliance Officer</option>
                    <option value="REGIONAL_OFFICER">Regional Officer</option>
                    <option value="BUREAU_AUTHORITY">Bureau Authority</option>
                    <option value="INSTITUTION">Institution User</option>
                    <option value="ADMIN">System Administrator</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Region</label>
                  <select
                    value={region}
                    onChange={(e) => setRegion(e.target.value)}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                  >
                    <option value="Northern">Northern</option>
                    <option value="Western">Western</option>
                    <option value="Southern">Southern</option>
                    <option value="Eastern">Eastern</option>
                    <option value="Head Office">Head Office</option>
                  </select>
                </div>
              </div>

              {role === 'INSTITUTION' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Link to Institution</label>
                  <select
                    value={institutionId}
                    onChange={(e) => setInstitutionId(e.target.value)}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                    required
                  >
                    <option value="">-- Choose Institution --</option>
                    {institutions.map((inst) => (
                      <option key={inst.id} value={inst.id}>
                        {inst.name} ({inst.aicte_id})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
