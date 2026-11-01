import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Bell, User, LogOut, CheckCircle, RefreshCw } from 'lucide-react';
import { apiRequest } from '../api/client';

export const Navbar: React.FC = () => {
  const { user, logout, switchRoleQuickLogin } = useAuth();
  const [notifications, setNotifications] = useState<any[]>([]);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const DEMO_ROLES = [
    { label: 'Institution: Apex Tech', email: 'institution@flowguard.aicte.gov.in', role: 'INSTITUTION' },
    { label: 'Institution: Saraswati Arch', email: 'saraswati@flowguard.aicte.gov.in', role: 'INSTITUTION' },
    { label: 'Institution: Greenfield Pharm', email: 'greenfield@flowguard.aicte.gov.in', role: 'INSTITUTION' },
    { label: 'Scrutiny Officer: Dr. Sen', email: 'scrutiny.officer@aicte.gov.in', role: 'SCRUTINY_OFFICER' },
    { label: 'EVC Coordinator: Prof. Rao', email: 'evc.coordinator@aicte.gov.in', role: 'EVC_COORDINATOR' },
    { label: 'Doc Verifier: Anil Kumar', email: 'doc.verifier@aicte.gov.in', role: 'DOCUMENT_VERIFIER' },
    { label: 'Compliance Officer: Pooja', email: 'compliance.officer@aicte.gov.in', role: 'COMPLIANCE_OFFICER' },
    { label: 'Regional Officer: Dr. Patel', email: 'regional.officer@aicte.gov.in', role: 'REGIONAL_OFFICER' },
    { label: 'Bureau Authority: Dr. Murthy', email: 'bureau.authority@aicte.gov.in', role: 'BUREAU_AUTHORITY' },
    { label: 'Administrator: Rajesh Sharma', email: 'admin@flowguard.aicte.gov.in', role: 'ADMIN' },
  ];

  const fetchNotifications = async () => {
    try {
      const data = await apiRequest<any[]>('/notifications');
      setNotifications(data || []);
      setUnreadCount(data?.filter(n => !n.is_read).length || 0);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 20000);
    return () => clearInterval(interval);
  }, [user]);

  const markAllRead = async () => {
    try {
      await apiRequest('/notifications/read-all', { method: 'POST' });
      fetchNotifications();
    } catch {
      // ignore
    }
  };

  const getPortalLabel = (role?: string) => {
    if (role === 'INSTITUTION') return 'Institution Portal';
    if (role === 'ADMIN') return 'Administration Portal';
    return 'Officials Portal';
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center p-1 shadow-xs">
            <img src="/logo-icon.png" alt="AICTE - FLOWW" className="w-8 h-8 object-contain" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-tight text-slate-900">AICTE - FLOWW</span>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-teal-100 text-teal-900 tracking-wider">
                {getPortalLabel(user?.role)}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 hidden sm:block">
              Integrated Approval Workflow, Compliance & Dual-Clock System
            </p>
          </div>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-3">
          {/* Quick Role Switcher for Evaluators / Hackathon Judges */}
          <div className="hidden lg:flex items-center gap-1.5 text-xs bg-slate-100 p-1 rounded-lg border border-slate-200">
            <span className="font-semibold text-slate-600 pl-2">Switch Demo Role:</span>
            <select
              value={user?.email || ''}
              onChange={(e) => switchRoleQuickLogin(e.target.value)}
              className="text-xs font-medium bg-white border border-slate-200 rounded px-2 py-1 text-slate-800 cursor-pointer"
            >
              {DEMO_ROLES.map((r, i) => (
                <option key={i} value={r.email}>
                  {r.label} ({r.role})
                </option>
              ))}
            </select>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifDropdown(!showNotifDropdown)}
              className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg relative cursor-pointer"
              title="Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 bg-red-600 text-white rounded-full text-[10px] font-bold flex items-center justify-center animate-pulse">
                  {unreadCount}
                </span>
              )}
            </button>

            {/* Dropdown */}
            {showNotifDropdown && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden z-50">
                <div className="p-3 bg-slate-900 text-white flex justify-between items-center">
                  <div className="text-xs font-bold">Notifications & Alerts ({notifications.length})</div>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllRead}
                      className="text-[11px] text-blue-300 hover:text-white cursor-pointer"
                    >
                      Mark all as read
                    </button>
                  )}
                </div>
                <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                  {notifications.length === 0 ? (
                    <div className="p-4 text-center text-xs text-slate-500">No notifications</div>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`p-3 text-xs hover:bg-slate-50 transition-colors ${!n.is_read ? 'bg-blue-50/50 font-medium' : ''}`}
                      >
                        <div className="flex justify-between items-start gap-2">
                          <span className={`font-semibold ${n.severity === 'CRITICAL' ? 'text-red-700' : 'text-slate-900'}`}>
                            {n.title}
                          </span>
                          <span className="text-[10px] text-slate-400 shrink-0 font-mono">
                            {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-slate-600 mt-1 text-[11px]">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User profile info & Logout */}
          <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
            <div className="hidden sm:block text-right">
              <div className="text-xs font-bold text-slate-900 leading-tight">{user?.full_name}</div>
              <div className="text-[11px] text-slate-500 font-mono">{user?.role}</div>
            </div>
            <button
              onClick={logout}
              title="Logout"
              className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg cursor-pointer"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
