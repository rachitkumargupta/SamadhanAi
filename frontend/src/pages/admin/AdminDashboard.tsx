import React from 'react';
import { useNavigate } from 'react-router-dom';
import { StatCard } from '../../components/ui/StatCard';
import { adminDashboardStats, complaintsByCategory, complaintsByStatus, weeklyTrend, mockDepartments } from '../../data/mockData';
import { FileText, CheckCircle, Clock, AlertTriangle, TrendingUp, Users, ArrowRight, Zap } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

export const AdminDashboard = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Admin Dashboard</h1>
        <p className="text-sm text-slate-500">System-wide complaint monitoring and analytics</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Complaints" value={adminDashboardStats.totalComplaints} icon={FileText} iconColor="text-blue-600" iconBg="bg-blue-50" trend={{ value: 12, positive: true }} />
        <StatCard title="Resolved" value={adminDashboardStats.resolvedComplaints} icon={CheckCircle} iconColor="text-green-600" iconBg="bg-green-50" trend={{ value: 8, positive: true }} />
        <StatCard title="Pending" value={adminDashboardStats.pendingComplaints} icon={Clock} iconColor="text-amber-600" iconBg="bg-amber-50" trend={{ value: 3, positive: false }} />
        <StatCard title="Escalated" value={adminDashboardStats.escalatedComplaints} icon={AlertTriangle} iconColor="text-red-600" iconBg="bg-red-50" trend={{ value: 5, positive: false }} />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Avg. Resolution" value={`${adminDashboardStats.avgResolutionDays}d`} subtitle="days" icon={TrendingUp} iconColor="text-violet-600" iconBg="bg-violet-50" />
        <StatCard title="SLA Breach Rate" value={`${adminDashboardStats.slaBreachRate}%`} icon={AlertTriangle} iconColor="text-orange-600" iconBg="bg-orange-50" />
        <StatCard title="Citizen Satisfaction" value={`${adminDashboardStats.citizenSatisfaction}%`} icon={Users} iconColor="text-teal-600" iconBg="bg-teal-50" />
        <StatCard title="AI Agents Active" value="3" subtitle="Analyst · Router · Monitor" icon={Zap} iconColor="text-blue-600" iconBg="bg-blue-50" />
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Weekly trend */}
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 mb-4">Weekly Complaint Trend</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={weeklyTrend} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }} />
              <Bar dataKey="submitted" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Submitted" />
              <Bar dataKey="resolved" fill="#22c55e" radius={[4, 4, 0, 0]} name="Resolved" />
            </BarChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-2 justify-center text-xs text-slate-500">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-blue-500 inline-block" />Submitted</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-green-500 inline-block" />Resolved</span>
          </div>
        </div>

        {/* By Category */}
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 mb-4">Complaints by Category</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={complaintsByCategory} dataKey="value" nameKey="label" cx="50%" cy="50%" outerRadius={70} innerRadius={40}>
                {complaintsByCategory.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12 }} />
              <Legend iconType="circle" iconSize={8} formatter={(v) => <span className="text-xs text-slate-600">{v}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Department overview */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-900">Department Overview</h2>
          <button onClick={() => navigate('/admin/departments')} className="text-xs text-blue-600 font-medium flex items-center gap-1">View all <ArrowRight className="w-3.5 h-3.5" /></button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-slate-100">
                <th className="pb-3 text-xs text-slate-400 font-medium">Department</th>
                <th className="pb-3 text-xs text-slate-400 font-medium text-right">Total</th>
                <th className="pb-3 text-xs text-slate-400 font-medium text-right">Resolved</th>
                <th className="pb-3 text-xs text-slate-400 font-medium text-right">Pending</th>
                <th className="pb-3 text-xs text-slate-400 font-medium text-right">Escalated</th>
                <th className="pb-3 text-xs text-slate-400 font-medium text-right">Avg Days</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {mockDepartments.map((d) => (
                <tr key={d.id} className="hover:bg-slate-50">
                  <td className="py-3 font-medium text-slate-800">{d.name}</td>
                  <td className="py-3 text-slate-600 text-right">{d.totalComplaints}</td>
                  <td className="py-3 text-green-600 text-right font-medium">{d.resolved}</td>
                  <td className="py-3 text-amber-600 text-right">{d.pending}</td>
                  <td className="py-3 text-red-600 text-right">{d.escalated}</td>
                  <td className="py-3 text-slate-600 text-right">{d.avgResolutionDays}d</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
