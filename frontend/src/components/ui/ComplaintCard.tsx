import React from 'react';
import { Complaint } from '../../types';
import { StatusBadge, SeverityBadge } from './Badge';
import { MapPin, Clock, ChevronRight } from 'lucide-react';
import { categoryLabels } from '../../data/mockData';
import { clsx } from 'clsx';

interface ComplaintCardProps {
  complaint: Complaint;
  onClick?: () => void;
  compact?: boolean;
}

export const ComplaintCard = ({ complaint, onClick, compact }: ComplaintCardProps) => {
  const date = new Date(complaint.createdAt);
  const daysAgo = Math.floor((Date.now() - date.getTime()) / 86_400_000);

  return (
    <div
      className={clsx(
        'card p-4 hover:shadow-md transition-shadow cursor-pointer group',
        complaint.slaBreached && 'border-l-4 border-l-red-500'
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-xs font-mono text-slate-400">{complaint.complaintId}</span>
            <StatusBadge status={complaint.status} />
            <SeverityBadge severity={complaint.severity} />
            {complaint.slaBreached && (
              <span className="badge bg-red-100 border border-red-200 text-red-700">SLA Breached</span>
            )}
          </div>
          <h3 className="font-semibold text-slate-800 text-sm leading-snug line-clamp-2">{complaint.title}</h3>
          {!compact && (
            <p className="text-xs text-slate-500 mt-1 line-clamp-2">{complaint.description}</p>
          )}
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-400 flex-wrap">
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {complaint.location.address}, {complaint.location.city}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {daysAgo === 0 ? 'Today' : `${daysAgo}d ago`}
            </span>
            <span className="px-1.5 py-0.5 bg-slate-100 rounded text-slate-500">
              {categoryLabels[complaint.category]}
            </span>
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500 shrink-0 mt-1 transition-colors" />
      </div>
      {complaint.assignedOfficerName && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-500">
          <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-[10px]">
            {complaint.assignedOfficerName[0]}
          </div>
          <span>Assigned to <strong>{complaint.assignedOfficerName}</strong> · {complaint.assignedDepartment}</span>
        </div>
      )}
    </div>
  );
};
