import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { mockComplaints, categoryLabels } from '../../data/mockData';
import { ComplaintTimeline } from '../../components/ui/ComplaintTimeline';
import { StatusBadge, SeverityBadge } from '../../components/ui/Badge';
import { ArrowLeft, MapPin, CheckCircle, User, Building, MessageSquare } from 'lucide-react';
import { clsx } from 'clsx';

export const OfficerComplaintDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [updating, setUpdating] = useState(false);
  const [updateMsg, setUpdateMsg] = useState('');
  const [newStatus, setNewStatus] = useState('');
  const complaint = mockComplaints.find((c) => c.id === id);

  if (!complaint) return <div className="text-center py-20"><p className="text-slate-500">Not found</p></div>;

  const handleUpdate = async () => {
    setUpdating(true);
    await new Promise((r) => setTimeout(r, 1000));
    setUpdating(false);
    setUpdateMsg('');
    setNewStatus('');
    alert('Status updated successfully! Citizens will be notified.');
  };

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <div className="card p-5">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <span className="text-xs font-mono text-slate-400">{complaint.complaintId}</span>
          <StatusBadge status={complaint.status} />
          <SeverityBadge severity={complaint.severity} />
          {complaint.slaBreached && <span className="badge bg-red-100 border border-red-200 text-red-700">SLA Breached</span>}
        </div>
        <h1 className="text-lg font-bold text-slate-900">{complaint.title}</h1>
        <p className="text-sm text-slate-600 mt-2">{complaint.description}</p>
        <div className="mt-4 flex flex-wrap gap-4 text-xs">
          <div><p className="text-slate-400">Category</p><p className="font-medium text-slate-700">{categoryLabels[complaint.category]}</p></div>
          <div><p className="text-slate-400">Citizen</p><p className="font-medium text-slate-700">{complaint.citizenName}</p></div>
          <div><p className="text-slate-400">Phone</p><p className="font-medium text-slate-700">{complaint.citizenPhone}</p></div>
          <div><p className="text-slate-400">Submitted</p><p className="font-medium text-slate-700">{new Date(complaint.createdAt).toLocaleDateString('en-IN')}</p></div>
          {complaint.slaDeadline && <div><p className="text-slate-400">SLA Deadline</p><p className={clsx('font-medium', complaint.slaBreached ? 'text-red-600' : 'text-slate-700')}>{new Date(complaint.slaDeadline).toLocaleDateString('en-IN')}</p></div>}
        </div>
      </div>

      {/* Location */}
      <div className="card p-5">
        <h2 className="font-semibold text-slate-900 flex items-center gap-2 mb-2"><MapPin className="w-4 h-4 text-slate-400" />Location</h2>
        <p className="text-sm text-slate-700">{complaint.location.address}</p>
        <p className="text-xs text-slate-400 mt-1">{complaint.location.ward && `${complaint.location.ward}, `}{complaint.location.city} {complaint.location.pincode}</p>
      </div>

      {/* Update Status Panel */}
      {!['resolved', 'closed'].includes(complaint.status) && (
        <div className="card p-5 border-l-4 border-l-violet-500">
          <h2 className="font-semibold text-slate-900 mb-4 flex items-center gap-2"><CheckCircle className="w-4 h-4 text-violet-500" />Update Complaint Status</h2>
          <div className="space-y-3">
            <div>
              <label className="label">New Status</label>
              <select className="input" value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
                <option value="">Select status...</option>
                <option value="in_progress">In Progress</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>
            <div>
              <label className="label">Update Message</label>
              <textarea className="input resize-none" rows={3} placeholder="Describe what action was taken..." value={updateMsg} onChange={(e) => setUpdateMsg(e.target.value)} />
            </div>
            <button className="btn-primary" onClick={handleUpdate} disabled={!newStatus || !updateMsg || updating}>
              {updating ? 'Updating...' : 'Submit Update'}
            </button>
          </div>
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
