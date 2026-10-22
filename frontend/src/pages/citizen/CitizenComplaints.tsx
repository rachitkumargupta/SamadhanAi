import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ComplaintCard } from '../../components/ui/ComplaintCard';
import { mockComplaints } from '../../data/mockData';
import { ComplaintStatus } from '../../types';
import { Search, SlidersHorizontal, PlusCircle } from 'lucide-react';

const statusOptions: { label: string; value: ComplaintStatus | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Pending', value: 'pending' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Escalated', value: 'escalated' },
  { label: 'Resolved', value: 'resolved' },
  { label: 'Closed', value: 'closed' },
];

export const CitizenComplaints = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ComplaintStatus | 'all'>('all');

  const myComplaints = mockComplaints.filter((c) => c.submittedBy === user?.id);
  const filtered = myComplaints.filter((c) => {
    const matchSearch = search === '' || c.title.toLowerCase().includes(search.toLowerCase()) || c.complaintId.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || c.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">My Complaints</h1>
          <p className="text-sm text-slate-500">{myComplaints.length} complaints total</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/citizen/submit')}>
          <PlusCircle className="w-4 h-4" /> Submit New
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input className="input pl-9" placeholder="Search by title or ID..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="flex gap-2 flex-wrap">
          {statusOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                statusFilter === opt.value
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-blue-300'
              }`}
            >{opt.label}</button>
          ))}
        </div>
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <div className="card p-10 text-center">
          <SlidersHorizontal className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No complaints found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((c) => (
            <ComplaintCard key={c.id} complaint={c} onClick={() => navigate(`/citizen/complaints/${c.id}`)} />
          ))}
        </div>
      )}
    </div>
  );
};
