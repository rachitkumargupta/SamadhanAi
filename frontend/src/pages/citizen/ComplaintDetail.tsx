import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { mockComplaints, categoryLabels, statusConfig, severityConfig } from '../../data/mockData';
import { ComplaintTimeline } from '../../components/ui/ComplaintTimeline';
import { StatusBadge, SeverityBadge } from '../../components/ui/Badge';
import { ArrowLeft, MapPin, User, Building, Clock, Bot, Brain, Info } from 'lucide-react';
import { clsx } from 'clsx';

export const ComplaintDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const complaint = mockComplaints.find((c) => c.id === id);

  if (!complaint) {
    return (
      <div className="text-center py-20">
        <p className="text-slate-500">Complaint not found</p>
        <button className="btn-primary mt-4" onClick={() => navigate(-1)}>Go Back</button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      {/* Header */}
      <div className="card p-5">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <span className="text-xs font-mono text-slate-400">{complaint.complaintId}</span>
          <StatusBadge status={complaint.status} />
          <SeverityBadge severity={complaint.severity} />
          {complaint.slaBreached && (
            <span className="badge bg-red-100 border border-red-200 text-red-700">SLA Breached</span>
          )}
        </div>
        <h1 className="text-lg font-bold text-slate-900">{complaint.title}</h1>
        <p className="text-sm text-slate-600 mt-2">{complaint.description}</p>

        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="text-xs">
            <p className="text-slate-400">Category</p>
            <p className="font-medium text-slate-700 mt-0.5">{categoryLabels[complaint.category]}</p>
          </div>
          <div className="text-xs">
            <p className="text-slate-400">Submitted</p>
            <p className="font-medium text-slate-700 mt-0.5">{new Date(complaint.createdAt).toLocaleDateString('en-IN')}</p>
          </div>
          {complaint.slaDeadline && (
            <div className="text-xs">
              <p className="text-slate-400">SLA Deadline</p>
              <p className={clsx('font-medium mt-0.5', complaint.slaBreached ? 'text-red-600' : 'text-slate-700')}>
                {new Date(complaint.slaDeadline).toLocaleDateString('en-IN')}
              </p>
            </div>
          )}
          <div className="text-xs">
            <p className="text-slate-400">Last Updated</p>
            <p className="font-medium text-slate-700 mt-0.5">{new Date(complaint.updatedAt).toLocaleDateString('en-IN')}</p>
          </div>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-5">
        {/* Location */}
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2 mb-3"><MapPin className="w-4 h-4 text-slate-400" />Location</h2>
          <p className="text-sm text-slate-700">{complaint.location.address}</p>
          {complaint.location.ward && <p className="text-xs text-slate-400 mt-1">{complaint.location.ward}</p>}
          <p className="text-xs text-slate-400">{complaint.location.city} {complaint.location.pincode}</p>
        </div>

        {/* Assignment */}
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2 mb-3"><Building className="w-4 h-4 text-slate-400" />Assignment</h2>
          {complaint.assignedDepartment ? (
            <>
              <p className="text-xs text-slate-400">Department</p>
              <p className="text-sm font-medium text-slate-700">{complaint.assignedDepartment}</p>
              {complaint.assignedOfficerName && (
                <>
                  <p className="text-xs text-slate-400 mt-2">Officer</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="w-6 h-6 rounded-full bg-violet-100 flex items-center justify-center text-violet-700 text-xs font-bold">{complaint.assignedOfficerName[0]}</div>
                    <p className="text-sm font-medium text-slate-700">{complaint.assignedOfficerName}</p>
                  </div>
                </>
              )}
            </>
          ) : (
            <p className="text-sm text-slate-400">Not yet assigned</p>
          )}
        </div>
      </div>

      {/* AI Analysis */}
      {complaint.aiAnalysis && (
        <div className="card p-5 border-l-4 border-l-purple-500">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2 mb-3">
            <Bot className="w-4 h-4 text-purple-500" />AI Analysis
            <span className="ml-auto badge bg-purple-50 border border-purple-200 text-purple-700">{Math.round(complaint.aiAnalysis.confidence * 100)}% confidence</span>
          </h2>
          <p className="text-sm text-slate-700 mb-3">{complaint.aiAnalysis.summary}</p>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs text-slate-400">Suggested Department</p>
              <p className="text-sm font-medium text-slate-700">{complaint.aiAnalysis.suggestedDepartment}</p>
            </div>
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs text-slate-400">SLA Given</p>
              <p className="text-sm font-medium text-slate-700">{complaint.aiAnalysis.suggestedSLA} hours</p>
            </div>
          </div>
          {complaint.aiAnalysis.missingInfo && complaint.aiAnalysis.missingInfo.length > 0 && (
            <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-xs text-amber-700 font-medium flex items-center gap-1"><Info className="w-3.5 h-3.5" />Missing Information Detected</p>
              <ul className="mt-1 space-y-0.5">
                {complaint.aiAnalysis.missingInfo.map((m, i) => <li key={i} className="text-xs text-amber-600">• {m}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Timeline */}
      <div className="card p-5">
        <h2 className="font-semibold text-slate-900 mb-4">Complaint Timeline</h2>
        <ComplaintTimeline events={complaint.timeline} />
      </div>
    </div>
  );
};
