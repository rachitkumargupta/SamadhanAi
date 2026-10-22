import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { StatCard } from '../../components/ui/StatCard';
import { ComplaintCard } from '../../components/ui/ComplaintCard';
import { mockComplaints } from '../../data/mockData';
import { FileText, CheckCircle, Clock, AlertTriangle, PlusCircle, ArrowRight } from 'lucide-react';

export const CitizenDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const myComplaints = mockComplaints.filter((c) => c.submittedBy === user?.id);
  const resolved = myComplaints.filter((c) => c.status === 'resolved' || c.status === 'closed').length;
  const pending = myComplaints.filter((c) => c.status === 'pending' || c.status === 'under_review' || c.status === 'assigned').length;
  const escalated = myComplaints.filter((c) => c.status === 'escalated').length;

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Welcome, {user?.name.split(' ')[0]} 👋</h1>
          <p className="text-sm text-slate-500 mt-0.5">Track your complaints and stay updated</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/citizen/submit')}>
          <PlusCircle className="w-4 h-4" />
          Submit Complaint
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Complaints" value={myComplaints.length} icon={FileText} iconColor="text-blue-600" iconBg="bg-blue-50" />
        <StatCard title="Resolved" value={resolved} icon={CheckCircle} iconColor="text-green-600" iconBg="bg-green-50" />
        <StatCard title="Pending" value={pending} icon={Clock} iconColor="text-amber-600" iconBg="bg-amber-50" />
        <StatCard title="Escalated" value={escalated} icon={AlertTriangle} iconColor="text-red-600" iconBg="bg-red-50" />
      </div>

      {/* Recent complaints */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">Recent Complaints</h2>
          <button
            onClick={() => navigate('/citizen/complaints')}
            className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
          >
            View all <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
        {myComplaints.length === 0 ? (
          <div className="text-center py-10">
            <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No complaints yet</p>
            <button className="btn-primary mt-4" onClick={() => navigate('/citizen/submit')}>
              Submit your first complaint
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {myComplaints.slice(0, 3).map((c) => (
              <ComplaintCard
                key={c.id}
                complaint={c}
                onClick={() => navigate(`/citizen/complaints/${c.id}`)}
              />
            ))}
          </div>
        )}
      </div>

      {/* How it works */}
      <div className="card p-5">
        <h2 className="font-semibold text-slate-900 mb-4">How Samadhan AI Works</h2>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {[
            { step: '01', title: 'Submit', desc: 'File your complaint with details' },
            { step: '02', title: 'Analyze', desc: 'AI classifies and prioritizes' },
            { step: '03', title: 'Route', desc: 'Assigned to right department' },
            { step: '04', title: 'Monitor', desc: 'SLA tracking, auto-escalation' },
            { step: '05', title: 'Resolve', desc: 'You get notified on closure' },
          ].map((s) => (
            <div key={s.step} className="text-center p-3 bg-slate-50 rounded-xl">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold mx-auto mb-2">{s.step}</div>
              <p className="text-xs font-semibold text-slate-800">{s.title}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
