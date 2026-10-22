import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ComplaintCard } from '../../components/ui/ComplaintCard';
import { mockComplaints } from '../../data/mockData';
import { ComplaintStatus } from '../../types';
import { Search } from 'lucide-react';

const statusOptions: { label: string; value: ComplaintStatus | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Assigned', value: 'assigned' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Escalated', value: 'escalated' },
  { label: 'Resolved', value: 'resolved' },
];

export const OfficerComplaints = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ComplaintStatus | 'all'>('all');

  const myComplaints = mockComplaints.filter((c) => c.assignedOfficer === user?.id);
  const filtered = myComplaints.filter((c) => {
    const matchSearch = !search || c.title.toLowerCase().includes(search.toLowerCase()) || c.complaintId.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || c.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Assigned Complaints</h1>
        <p className="text-sm text-slate-500">{myComplaints.length} complaints assigned to you</p>
      </div>
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input className="input pl-9" placeholder="Search complaints..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="flex gap-2 flex-wrap">
          {statusOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                statusFilter === opt.value ? 'bg-violet-600 text-white border-violet-600' : 'bg-white text-slate-600 border-slate-200 hover:border-violet-300'
              }`}
            >{opt.label}</button>
          ))}
        </div>
      </div>
      <div className="space-y-3">
        {filtered.map((c) => (
          <ComplaintCard key={c.id} complaint={c} onClick={() => navigate(`/officer/complaints/${c.id}`)} />
        ))}
        {filtered.length === 0 && (
          <div className="card p-10 text-center text-slate-400 text-sm">No complaints found</div>
        )}
      </div>
    </div>
  );
};
