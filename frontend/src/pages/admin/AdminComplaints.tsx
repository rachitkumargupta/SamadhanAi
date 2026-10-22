import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ComplaintCard } from '../../components/ui/ComplaintCard';
import { mockComplaints } from '../../data/mockData';
import { ComplaintStatus, ComplaintCategory } from '../../types';
import { categoryLabels } from '../../data/mockData';
import { Search, Filter } from 'lucide-react';

export const AdminComplaints = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ComplaintStatus | 'all'>('all');
  const [categoryFilter, setCategoryFilter] = useState<ComplaintCategory | 'all'>('all');

  const filtered = mockComplaints.filter((c) => {
    const matchSearch = !search || c.title.toLowerCase().includes(search.toLowerCase()) || c.complaintId.toLowerCase().includes(search.toLowerCase()) || c.citizenName.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || c.status === statusFilter;
    const matchCat = categoryFilter === 'all' || c.category === categoryFilter;
    return matchSearch && matchStatus && matchCat;
  });

  const statuses: { label: string; value: ComplaintStatus | 'all' }[] = [
    { label: 'All', value: 'all' }, { label: 'Pending', value: 'pending' },
    { label: 'In Progress', value: 'in_progress' }, { label: 'Escalated', value: 'escalated' },
    { label: 'Resolved', value: 'resolved' }, { label: 'Closed', value: 'closed' },
  ];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-900">All Complaints</h1>
        <p className="text-sm text-slate-500">{filtered.length} of {mockComplaints.length} complaints</p>
      </div>
      <div className="card p-4 space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input className="input pl-9" placeholder="Search by title, ID, or citizen name..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="flex flex-wrap gap-2">
          <Filter className="w-4 h-4 text-slate-400 self-center" />
          {statuses.map((s) => (
            <button key={s.value} onClick={() => setStatusFilter(s.value)}
              className={`px-3 py-1 rounded-lg text-xs font-medium border transition-colors ${
                statusFilter === s.value ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-slate-600 border-slate-200 hover:border-emerald-300'
              }`}>{s.label}</button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-slate-400 self-center">Category:</span>
          <button onClick={() => setCategoryFilter('all')} className={`px-2.5 py-1 rounded-lg text-xs border transition-colors ${
            categoryFilter === 'all' ? 'bg-slate-700 text-white border-slate-700' : 'bg-white text-slate-600 border-slate-200'
          }`}>All</button>
          {(Object.entries(categoryLabels) as [ComplaintCategory, string][]).map(([k, v]) => (
            <button key={k} onClick={() => setCategoryFilter(k)} className={`px-2.5 py-1 rounded-lg text-xs border transition-colors ${
              categoryFilter === k ? 'bg-slate-700 text-white border-slate-700' : 'bg-white text-slate-600 border-slate-200'
            }`}>{v}</button>
          ))}
        </div>
      </div>
      <div className="space-y-3">
        {filtered.map((c) => (
          <ComplaintCard key={c.id} complaint={c} onClick={() => navigate(`/admin/complaints/${c.id}`)} />
        ))}
        {filtered.length === 0 && <div className="card p-10 text-center text-slate-400 text-sm">No complaints match your filters</div>}
      </div>
    </div>
  );
};
