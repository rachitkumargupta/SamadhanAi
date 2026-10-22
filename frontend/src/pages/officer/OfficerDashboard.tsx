import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { StatCard } from '../../components/ui/StatCard';
import { ComplaintCard } from '../../components/ui/ComplaintCard';
import { mockComplaints, mockOfficers } from '../../data/mockData';
import { FileText, CheckCircle, Clock, AlertTriangle, ArrowRight, TrendingUp } from 'lucide-react';

export const OfficerDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const officer = mockOfficers.find((o) => o.id === user?.id);
  const myComplaints = mockComplaints.filter((c) => c.assignedOfficer === user?.id);
  const pending = myComplaints.filter((c) => ['assigned', 'in_progress', 'under_review'].includes(c.status)).length;
  const resolved = myComplaints.filter((c) => ['resolved', 'closed'].includes(c.status)).length;
  const escalated = myComplaints.filter((c) => c.status === 'escalated').length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Officer Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">{user?.name} · {user?.department}</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Assigned" value={myComplaints.length} icon={FileText} iconColor="text-blue-600" iconBg="bg-blue-50" />
        <StatCard title="In Progress" value={pending} icon={Clock} iconColor="text-amber-600" iconBg="bg-amber-50" />
        <StatCard title="Resolved" value={resolved} icon={CheckCircle} iconColor="text-green-600" iconBg="bg-green-50" />
        <StatCard title="Escalated" value={escalated} icon={AlertTriangle} iconColor="text-red-600" iconBg="bg-red-50" />
      </div>

      {/* Performance card */}
      {officer && (
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2 mb-4"><TrendingUp className="w-4 h-4 text-slate-400" />My Performance</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-blue-700">{officer.resolvedComplaints}</p>
              <p className="text-xs text-blue-500 mt-1">Total Resolved</p>
            </div>
            <div className="bg-amber-50 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-amber-700">{officer.pendingComplaints}</p>
              <p className="text-xs text-amber-500 mt-1">Pending</p>
            </div>
            <div className="bg-red-50 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-red-700">{officer.slaBreaches}</p>
              <p className="text-xs text-red-500 mt-1">SLA Breaches</p>
            </div>
            <div className="bg-green-50 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-green-700">{officer.resolvedComplaints > 0 ? Math.round((officer.resolvedComplaints / officer.assignedComplaints) * 100) : 0}%</p>
              <p className="text-xs text-green-500 mt-1">Resolution Rate</p>
            </div>
          </div>
        </div>
      )}

      {/* Assigned complaints */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">Assigned Complaints</h2>
          <button onClick={() => navigate('/officer/complaints')} className="text-xs text-blue-600 font-medium flex items-center gap-1">
            View all <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
        {myComplaints.length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-8">No complaints assigned yet</p>
        ) : (
          <div className="space-y-3">
            {myComplaints.slice(0, 4).map((c) => (
              <ComplaintCard key={c.id} complaint={c} onClick={() => navigate(`/officer/complaints/${c.id}`)} compact />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
