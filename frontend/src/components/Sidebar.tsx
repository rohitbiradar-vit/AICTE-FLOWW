import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, FileText, PlusCircle, FolderCheck, CheckSquare,
  CalendarCheck, ShieldAlert, Users, GitBranch, History, Clock, FileCheck
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role;

  const institutionLinks = [
    { to: '/institution/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/institution/applications', label: 'Applications', icon: FileText },
    { to: '/institution/applications/new', label: 'New Application', icon: PlusCircle },
    { to: '/institution/documents', label: 'Document Vault', icon: FolderCheck },
    { to: '/institution/compliance', label: 'Compliance & Undertakings', icon: CheckSquare },
    { to: '/institution/evc', label: 'EVC Visit Schedule', icon: CalendarCheck },
  ];

  const officialLinks = [
    { to: '/official/dashboard', label: 'Scrutiny Dashboard', icon: LayoutDashboard },
    { to: '/official/work-queue', label: 'Application Work Queue', icon: FileText },
    { to: '/official/evc', label: 'EVC Visit Management', icon: CalendarCheck },
    { to: '/official/compliance', label: 'Compliance Verifications', icon: CheckSquare },
    { to: '/official/expiry-register', label: 'Document Expiry Register', icon: Clock },
  ];

  const adminLinks = [
    { to: '/admin/dashboard', label: 'System Overview', icon: LayoutDashboard },
    { to: '/admin/users', label: 'User & Role Management', icon: Users },
    { to: '/admin/workflows', label: 'Workflow & SLA Rules', icon: GitBranch },
    { to: '/admin/audit-logs', label: 'Audit Trail & Logs', icon: History },
  ];

  let links = institutionLinks;
  if (role === 'ADMIN') {
    links = adminLinks;
  } else if (role !== 'INSTITUTION') {
    links = officialLinks;
  }

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 min-h-[calc(100vh-4rem)] flex flex-col shrink-0">
      <div className="p-4 border-b border-slate-800">
        <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Active Workspace</div>
        <div className="text-sm font-semibold text-white truncate mt-0.5">
          {user?.institution_name || (user?.role === 'ADMIN' ? 'Headquarters Admin' : `${user?.role} Queue`)}
        </div>
      </div>

      <nav className="p-3 space-y-1 flex-1">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{link.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800 text-[11px] text-slate-500">
        <div>AICTE - FLOWW v1.0.0</div>
        <div>SIH Problem Statement 26262</div>
      </div>
    </aside>
  );
};
