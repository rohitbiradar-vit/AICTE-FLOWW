import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Login } from './pages/Login';

// Institution pages
import { InstitutionDashboard } from './pages/institution/InstitutionDashboard';
import { ApplicationList } from './pages/institution/ApplicationList';
import { ApplicationCreate } from './pages/institution/ApplicationCreate';
import { ApplicationDetail } from './pages/institution/ApplicationDetail';
import { DocumentManager } from './pages/institution/DocumentManager';
import { CompliancePortal } from './pages/institution/CompliancePortal';
import { InstitutionEVCView } from './pages/institution/InstitutionEVCView';

// Official pages
import { OfficialDashboard } from './pages/official/OfficialDashboard';
import { WorkQueue } from './pages/official/WorkQueue';
import { ApplicationReview } from './pages/official/ApplicationReview';
import { EVCManagement } from './pages/official/EVCManagement';
import { ComplianceReview } from './pages/official/ComplianceReview';

// Admin pages
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { UserManagement } from './pages/admin/UserManagement';
import { WorkflowConfig } from './pages/admin/WorkflowConfig';
import { AuditLogs } from './pages/admin/AuditLogs';

const ProtectedLayout: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-xs text-slate-500">Checking authentication...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

const RootRedirect: React.FC = () => {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;

  if (user.role === 'INSTITUTION') {
    return <Navigate to="/institution/dashboard" replace />;
  } else if (user.role === 'ADMIN') {
    return <Navigate to="/admin/dashboard" replace />;
  } else {
    return <Navigate to="/official/dashboard" replace />;
  }
};

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedLayout />}>
            <Route index element={<RootRedirect />} />

            {/* Institution Portal */}
            <Route path="institution/dashboard" element={<InstitutionDashboard />} />
            <Route path="institution/applications" element={<ApplicationList />} />
            <Route path="institution/applications/new" element={<ApplicationCreate />} />
            <Route path="institution/applications/:id" element={<ApplicationDetail />} />
            <Route path="institution/documents" element={<DocumentManager />} />
            <Route path="institution/compliance" element={<CompliancePortal />} />
            <Route path="institution/compliance/:id" element={<CompliancePortal />} />
            <Route path="institution/evc" element={<InstitutionEVCView />} />

            {/* Officials Portal */}
            <Route path="official/dashboard" element={<OfficialDashboard />} />
            <Route path="official/work-queue" element={<WorkQueue />} />
            <Route path="official/applications/:id" element={<ApplicationReview />} />
            <Route path="official/evc" element={<EVCManagement />} />
            <Route path="official/compliance" element={<ComplianceReview />} />
            <Route path="official/expiry-register" element={<ComplianceReview />} />

            {/* Administration Portal */}
            <Route path="admin/dashboard" element={<AdminDashboard />} />
            <Route path="admin/users" element={<UserManagement />} />
            <Route path="admin/workflows" element={<WorkflowConfig />} />
            <Route path="admin/audit-logs" element={<AuditLogs />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
