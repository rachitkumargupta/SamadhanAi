import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { ComplaintRead } from '../types';
import { Search, Loader2, ArrowRight } from 'lucide-react';

interface GrievanceHistoryPageProps {
  onSelectComplaint: (ref: string) => void;
}

export const GrievanceHistoryPage: React.FC<GrievanceHistoryPageProps> = ({ onSelectComplaint }) => {
  const [complaints, setComplaints] = useState<ComplaintRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadComplaints();
  }, []);

  const loadComplaints = async () => {
    try {
      setLoading(true);
      const res = await api.getComplaints(50, 0);
      setComplaints(res.items);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = complaints.filter(c => {
    const matchesFilter = filter === 'ALL' || c.status.toUpperCase() === filter;
    const matchesSearch = 
      c.public_reference.toLowerCase().includes(search.toLowerCase()) ||
      (c.location_text && c.location_text.toLowerCase().includes(search.toLowerCase())) ||
      (c.description && c.description.toLowerCase().includes(search.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-6">
      
      {/* Top Bar with Search & Filters */}
      <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ID, location, or keyword..."
            className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-400 dark:border-slate-600 pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:border-blue-700"
          />
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-medium">Filter Status:</span>
          {['ALL', 'SUBMITTED', 'IN_PROGRESS', 'RESOLVED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilter(st)}
              className={`px-3 py-1 text-xs font-semibold border transition ${
                filter === st
                  ? 'bg-[#0b2545] text-white border-[#06182c]'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:bg-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

      </div>

      {/* Complaints Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 shadow-sm transition-colors">
        <div className="bg-slate-100 dark:bg-slate-800 px-6 py-3 border-b border-slate-300 dark:border-slate-700 flex items-center justify-between">
          <h2 className="text-xs font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">
            Registered Grievances Log
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            Total Records: {filtered.length}
          </span>
        </div>

        <div className="p-6 overflow-x-auto">
          {loading ? (
            <div className="p-12 text-center text-xs text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-700" />
              <span>Fetching grievances...</span>
            </div>
          ) : filtered.length > 0 ? (
            <table className="w-full text-xs border border-slate-300 dark:border-slate-700 text-left">
              <thead className="bg-slate-100 dark:bg-slate-800 font-bold border-b border-slate-300 dark:border-slate-700">
                <tr>
                  <th className="p-3 border-r border-slate-300 dark:border-slate-700 w-12 text-center">S.No</th>
                  <th className="p-3 border-r border-slate-300 dark:border-slate-700 w-36 font-mono">Registration No.</th>
                  <th className="p-3 border-r border-slate-300 dark:border-slate-700 w-44">Date Logged</th>
                  <th className="p-3 border-r border-slate-300 dark:border-slate-700">Location & Details</th>
                  <th className="p-3 border-r border-slate-300 dark:border-slate-700 w-32 text-center">Status</th>
                  <th className="p-3 w-28 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-300 dark:divide-slate-700">
                {filtered.map((item, index) => (
                  <tr key={item.public_reference} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="p-3 border-r border-slate-300 dark:border-slate-700 text-center font-medium">
                      {index + 1}
                    </td>
                    <td className="p-3 border-r border-slate-300 dark:border-slate-700 font-mono font-bold text-blue-700 dark:text-blue-400">
                      {item.public_reference}
                    </td>
                    <td className="p-3 border-r border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400">
                      {new Date(item.created_at).toLocaleDateString()} {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="p-3 border-r border-slate-300 dark:border-slate-700">
                      <p className="font-semibold text-slate-800 dark:text-slate-200">{item.location_text || 'Coordinates on file'}</p>
                      {item.description && (
                        <p className="text-slate-500 dark:text-slate-400 truncate max-w-md mt-0.5">{item.description}</p>
                      )}
                    </td>
                    <td className="p-3 border-r border-slate-300 dark:border-slate-700 text-center">
                      <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-300 border border-blue-300">
                        {item.status}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <button
                        onClick={() => onSelectComplaint(item.public_reference)}
                        className="inline-flex items-center gap-1 text-xs font-bold text-blue-700 dark:text-blue-400 hover:underline"
                      >
                        <span>Track</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center text-xs text-slate-500">
              No registered grievances found matching the criteria.
            </div>
          )}
        </div>
      </div>

    </div>
  );
};
