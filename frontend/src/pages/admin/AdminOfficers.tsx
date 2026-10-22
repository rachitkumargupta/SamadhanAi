import React from 'react';
import { mockOfficers } from '../../data/mockData';
import { Shield, Phone, Mail, AlertTriangle, CheckCircle } from 'lucide-react';
import { clsx } from 'clsx';

export const AdminOfficers = () => {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Officers</h1>
        <p className="text-sm text-slate-500">{mockOfficers.length} officers registered</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {mockOfficers.map((officer) => {
          const resRate = officer.assignedComplaints > 0 ? Math.round((officer.resolvedComplaints / officer.assignedComplaints) * 100) : 0;
          return (
            <div key={officer.id} className="card p-5">
              <div className="flex items-start gap-3 mb-4">
                <div className={clsx('w-10 h-10 rounded-full flex items-center justify-center text-white font-bold shrink-0', officer.status === 'active' ? 'bg-violet-600' : 'bg-slate-300')}>
                  {officer.name[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-slate-900 text-sm">{officer.name}</h3>
                    <span className={clsx('badge', officer.status === 'active' ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-slate-100 text-slate-500')}>{officer.status}</span>
                  </div>
                  <p className="text-xs text-slate-400">{officer.department}</p>
                </div>
              </div>
              <div className="space-y-1.5 mb-4">
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Mail className="w-3.5 h-3.5" />
                  <span>{officer.email}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Phone className="w-3.5 h-3.5" />
                  <span>{officer.phone}</span>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-2 text-center">
                <div className="bg-blue-50 rounded-lg p-2">
                  <p className="text-sm font-bold text-blue-700">{officer.assignedComplaints}</p>
                  <p className="text-[10px] text-blue-400">Assigned</p>
                </div>
                <div className="bg-green-50 rounded-lg p-2">
                  <p className="text-sm font-bold text-green-700">{officer.resolvedComplaints}</p>
                  <p className="text-[10px] text-green-400">Resolved</p>
                </div>
                <div className="bg-amber-50 rounded-lg p-2">
                  <p className="text-sm font-bold text-amber-700">{officer.pendingComplaints}</p>
                  <p className="text-[10px] text-amber-400">Pending</p>
                </div>
                <div className={clsx('rounded-lg p-2', officer.slaBreaches > 0 ? 'bg-red-50' : 'bg-slate-50')}>
                  <p className={clsx('text-sm font-bold', officer.slaBreaches > 0 ? 'text-red-700' : 'text-slate-500')}>{officer.slaBreaches}</p>
                  <p className="text-[10px] text-slate-400">SLA Breach</p>
                </div>
              </div>
              <div className="mt-3">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-500">Resolution Rate</span>
                  <span className="font-medium text-slate-700">{resRate}%</span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-violet-500 rounded-full" style={{ width: `${resRate}%` }} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
