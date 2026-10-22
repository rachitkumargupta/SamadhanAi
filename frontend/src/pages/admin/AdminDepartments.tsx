import React from 'react';
import { mockDepartments } from '../../data/mockData';
import { Building, TrendingUp, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

export const AdminDepartments = () => {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Departments</h1>
        <p className="text-sm text-slate-500">{mockDepartments.length} departments in the system</p>
      </div>
      <div className="grid gap-4">
        {mockDepartments.map((dept) => {
          const resolvedPct = Math.round((dept.resolved / dept.totalComplaints) * 100);
          return (
            <div key={dept.id} className="card p-5">
              <div className="flex items-start gap-4 flex-wrap">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
                  <Building className="w-5 h-5 text-emerald-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap mb-1">
                    <h3 className="font-semibold text-slate-900">{dept.name}</h3>
                    <span className="badge bg-slate-100 text-slate-500">{dept.code}</span>
                  </div>
                  <p className="text-xs text-slate-400">Head: {dept.head}</p>
                  {/* Progress bar */}
                  <div className="mt-3">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-500">Resolution Progress</span>
                      <span className="font-medium text-slate-700">{resolvedPct}%</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500 rounded-full transition-all" style={{ width: `${resolvedPct}%` }} />
                    </div>
                  </div>
                </div>
                <div className="flex gap-4 text-center shrink-0">
                  <div>
                    <p className="text-lg font-bold text-slate-900">{dept.totalComplaints}</p>
                    <p className="text-xs text-slate-400">Total</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-green-600">{dept.resolved}</p>
                    <p className="text-xs text-slate-400">Resolved</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-amber-600">{dept.pending}</p>
                    <p className="text-xs text-slate-400">Pending</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-red-600">{dept.escalated}</p>
                    <p className="text-xs text-slate-400">Escalated</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-violet-600">{dept.avgResolutionDays}d</p>
                    <p className="text-xs text-slate-400">Avg Days</p>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
