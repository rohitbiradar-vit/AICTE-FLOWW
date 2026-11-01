import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Shield, Building2, UserCheck, Settings, ArrowRight, Lock, Mail } from 'lucide-react';

export const Login: React.FC = () => {
  const { login, switchRoleQuickLogin } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (roleEmail: string, redirectPath: string) => {
    setError('');
    setLoading(true);
    try {
      await switchRoleQuickLogin(roleEmail);
      navigate(redirectPath);
    } catch (err: any) {
      setError(err.message || 'Quick login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex p-3 rounded-2xl bg-white border border-slate-700/50 mb-4 shadow-xl shadow-teal-950/40">
          <img src="/logo-icon.png" alt="AICTE - FLOWW" className="w-16 h-16 object-contain" />
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight text-white">AICTE - FLOWW</h2>
        <p className="mt-2 text-xs text-slate-400 max-w-sm mx-auto">
          Integrated Approval Workflow Automation, Statutory Compliance & Dual-Clock Engine
        </p>
        <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-950 text-blue-300 border border-blue-800/60 font-mono">
          SIH Problem Statement 26262 | Regulation Bureau
        </span>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-4xl px-4">
        {/* Quick Portal Switcher Cards for Evaluators */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {/* Card 1: Institution */}
          <div className="bg-slate-900 border border-slate-800 hover:border-amber-500/40 rounded-xl p-5 transition-all flex flex-col justify-between">
            <div>
              <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg w-fit mb-3">
                <Building2 className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-white">1. Institution Portal</h3>
              <p className="text-xs text-slate-400 mt-1">
                For colleges: create & submit approval applications, upload docs, track clocks, and submit compliance.
              </p>
            </div>
            <button
              onClick={() => handleQuickLogin('institution@flowguard.aicte.gov.in', '/institution/dashboard')}
              className="mt-4 w-full py-2 bg-amber-600/90 hover:bg-amber-600 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
            >
              Enter as Institution (Apex Tech) <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Card 2: Officials */}
          <div className="bg-slate-900 border border-slate-800 hover:border-blue-500/40 rounded-xl p-5 transition-all flex flex-col justify-between">
            <div>
              <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg w-fit mb-3">
                <UserCheck className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-white">2. AICTE Officials Portal</h3>
              <p className="text-xs text-slate-400 mt-1">
                For officers: work queue, AI scrutiny report review, EVC scheduling, undertakings verification, and transitions.
              </p>
            </div>
            <div className="space-y-1.5 mt-4">
              <button
                onClick={() => handleQuickLogin('scrutiny.officer@aicte.gov.in', '/official/dashboard')}
                className="w-full py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-md text-xs font-semibold flex items-center justify-center gap-1 cursor-pointer"
              >
                Scrutiny Officer <ArrowRight className="w-3 h-3" />
              </button>
              <button
                onClick={() => handleQuickLogin('evc.coordinator@aicte.gov.in', '/official/evc')}
                className="w-full py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md text-xs font-semibold flex items-center justify-center gap-1 cursor-pointer"
              >
                EVC Coordinator <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>

          {/* Card 3: Administration */}
          <div className="bg-slate-900 border border-slate-800 hover:border-emerald-500/40 rounded-xl p-5 transition-all flex flex-col justify-between">
            <div>
              <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg w-fit mb-3">
                <Settings className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-white">3. System Administration</h3>
              <p className="text-xs text-slate-400 mt-1">
                For administrators: configure workflow rules, SLA deadlines, user roles, holidays, and export audit trails.
              </p>
            </div>
            <button
              onClick={() => handleQuickLogin('admin@flowguard.aicte.gov.in', '/admin/dashboard')}
              className="mt-4 w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
            >
              Enter as Admin <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Standard Manual Login Form */}
        <div className="bg-slate-900 py-8 px-6 shadow-xl rounded-2xl border border-slate-800 max-w-md mx-auto">
          <h3 className="text-sm font-bold text-slate-200 mb-4 text-center">Or Sign in with Custom Credentials</h3>
          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-200 text-xs">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Official / Institutional Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@aicte.gov.in"
                  required
                  className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-hidden focus:border-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-hidden focus:border-blue-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer shadow-md mt-2"
            >
              {loading ? 'Authenticating...' : 'Sign In to AICTE - FLOWW'}
            </button>
          </form>

          <div className="mt-4 pt-4 border-t border-slate-800 text-center text-[11px] text-slate-500">
            Demo password for all accounts: <code className="text-slate-300">DemoPass123!</code>
          </div>
        </div>
      </div>
    </div>
  );
};
