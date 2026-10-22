import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppShell } from './components/layout/AppShell';

// Pages
import { LoginPage } from './pages/LoginPage';

// Citizen
import { CitizenDashboard } from './pages/citizen/CitizenDashboard';
import { CitizenComplaints } from './pages/citizen/CitizenComplaints';
import { SubmitComplaint } from './pages/citizen/SubmitComplaint';
import { ComplaintDetail } from './pages/citizen/ComplaintDetail';

// Officer
import { OfficerDashboard } from './pages/officer/OfficerDashboard';
import { OfficerComplaints } from './pages/officer/OfficerComplaints';
import { OfficerComplaintDetail } from './pages/officer/OfficerComplaintDetail';

// Admin
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { AdminComplaints } from './pages/admin/AdminComplaints';
import { AdminComplaintDetail } from './pages/admin/AdminComplaintDetail';
import { AdminDepartments } from './pages/admin/AdminDepartments';
import { AdminOfficers } from './pages/admin/AdminOfficers';

// Route guard
const ProtectedRoute = ({ children, requiredRole }: { children: React.ReactNode; requiredRole?: string }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (requiredRole && user.role !== requiredRole) return <Navigate to="/login" replace />;
  return <AppShell>{children}</AppShell>;
};

const AppRoutes = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={`/${user.role}`} replace /> : <LoginPage />} />

      {/* Citizen routes */}
      <Route path="/citizen" element={<ProtectedRoute requiredRole="citizen"><CitizenDashboard /></ProtectedRoute>} />
      <Route path="/citizen/complaints" element={<ProtectedRoute requiredRole="citizen"><CitizenComplaints /></ProtectedRoute>} />
      <Route path="/citizen/complaints/:id" element={<ProtectedRoute requiredRole="citizen"><ComplaintDetail /></ProtectedRoute>} />
      <Route path="/citizen/submit" element={<ProtectedRoute requiredRole="citizen"><SubmitComplaint /></ProtectedRoute>} />

      {/* Officer routes */}
      <Route path="/officer" element={<ProtectedRoute requiredRole="officer"><OfficerDashboard /></ProtectedRoute>} />
      <Route path="/officer/complaints" element={<ProtectedRoute requiredRole="officer"><OfficerComplaints /></ProtectedRoute>} />
      <Route path="/officer/complaints/:id" element={<ProtectedRoute requiredRole="officer"><OfficerComplaintDetail /></ProtectedRoute>} />

      {/* Admin routes */}
      <Route path="/admin" element={<ProtectedRoute requiredRole="admin"><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin/complaints" element={<ProtectedRoute requiredRole="admin"><AdminComplaints /></ProtectedRoute>} />
      <Route path="/admin/complaints/:id" element={<ProtectedRoute requiredRole="admin"><AdminComplaintDetail /></ProtectedRoute>} />
      <Route path="/admin/departments" element={<ProtectedRoute requiredRole="admin"><AdminDepartments /></ProtectedRoute>} />
      <Route path="/admin/officers" element={<ProtectedRoute requiredRole="admin"><AdminOfficers /></ProtectedRoute>} />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
