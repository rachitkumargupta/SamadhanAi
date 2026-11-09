import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { 
  ComplaintRead, 
  ComplaintAnalysisStatusRead, 
  ComplaintEventRead 
} from '../types';
import { Search, Loader2 } from 'lucide-react';

interface GrievanceStatusPageProps {
  initialReference?: string;
}

export const GrievanceStatusPage: React.FC<GrievanceStatusPageProps> = ({
  initialReference = 'CMP/2026/08912'
}) => {
  const [reference, setReference] = useState(initialReference);
  const [searchInput, setSearchInput] = useState(initialReference);

  const [complaint, setComplaint] = useState<ComplaintRead | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<ComplaintAnalysisStatusRead | null>(null);
  const [events, setEvents] = useState<ComplaintEventRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmedClosed, setConfirmedClosed] = useState(false);
  const [disputed, setDisputed] = useState(false);

  const loadData = async (ref: string) => {
    if (!ref.trim()) return;
    try {
      setLoading(true);
      setError(null);
      const [comp, evt] = await Promise.all([
        api.getComplaint(ref),
        api.getEvents(ref).catch(() => ({ items: [] }))
      ]);
      setComplaint(comp);
      setEvents(evt.items);

      try {
        const analysis = await api.getAnalysis(ref);
        setAnalysisStatus(analysis);
      } catch {
        setAnalysisStatus(null);
      }
    } catch (err: any) {
      setError(err.message || 'Grievance not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(reference);
  }, [reference]);

  useEffect(() => {
    if (!complaint || !analysisStatus) return;
    if (analysisStatus.status !== 'pending' && analysisStatus.status !== 'running') return;

    const timer = setInterval(async () => {
      try {
        const updated = await api.getAnalysis(reference);
        setAnalysisStatus(updated);
        if (updated.status === 'completed' || updated.status === 'failed') {
          clearInterval(timer);
        }
      } catch {
        // Continue
      }
    }, 2500);

    return () => clearInterval(timer);
  }, [analysisStatus?.status, reference, complaint]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setReference(searchInput.trim());
    }
  };

  const getStatusBadge = (status: string) => {
    if (confirmedClosed) {
      return (
        <span className="px-3 py-1 bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 text-xs font-bold uppercase">
          CITIZEN CONFIRMED & CLOSED
        </span>
      );
    }
    if (disputed) {
      return (
        <span className="px-3 py-1 bg-rose-100 text-rose-900 dark:bg-rose-950 dark:text-rose-300 border border-rose-300 text-xs font-bold uppercase">
          DISPUTED - INDEPENDENT REVIEW
        </span>
      );
    }
    return (
      <span className="px-3 py-1 bg-blue-100 text-blue-900 dark:bg-blue-950 dark:text-blue-300 border border-blue-300 text-xs font-bold uppercase">
        {status || 'CASE UNDER INVESTIGATION'}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      
      {/* Search Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearch} className="flex-1 flex gap-2 w-full">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Enter Grievance Registration Number (e.g. CMP/2026/08912)..."
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-400 dark:border-slate-600 pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:border-blue-700 font-mono"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-2 bg-[#0b2545] hover:bg-[#134074] text-white text-xs font-bold uppercase tracking-wider"
          >
            Track Status
          </button>
        </form>

        <div className="text-xs text-slate-500 shrink-0">
          Viewing Record: <strong className="font-mono text-slate-800 dark:text-slate-200">{reference}</strong>
        </div>
      </div>

      {loading && !complaint && (
        <div className="p-12 text-center text-xs text-slate-500 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-700" />
          <span>Retrieving official municipal grievance record...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-950/40 border border-red-300 dark:border-red-800 text-red-800 dark:text-red-300 text-xs">
          {error}
        </div>
      )}

      {complaint && (
        <>
          {/* Official Grievance Summary Table */}
          <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 shadow-sm transition-colors">
            <div className="bg-slate-100 dark:bg-slate-800 px-6 py-3 border-b border-slate-300 dark:border-slate-700 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xs font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">
                Grievance Status Details
              </h2>
              {getStatusBadge(complaint.status)}
            </div>

            <div className="p-6">
              <table className="w-full text-xs border border-slate-300 dark:border-slate-700 text-left">
                <tbody>
                  <tr className="border-b border-slate-300 dark:border-slate-700">
                    <th className="bg-slate-50 dark:bg-slate-800/60 p-3 font-bold w-1/4 border-r border-slate-300 dark:border-slate-700">
                      Registration Number
                    </th>
                    <td className="p-3 font-mono font-bold text-blue-700 dark:text-blue-400 w-1/4 border-r border-slate-300 dark:border-slate-700 text-sm">
                      {complaint.public_reference}
                    </td>
                    <th className="bg-slate-50 dark:bg-slate-800/60 p-3 font-bold w-1/4 border-r border-slate-300 dark:border-slate-700">
                      Date of Registration
                    </th>
                    <td className="p-3 w-1/4 font-medium">
                      {new Date(complaint.created_at).toLocaleString()}
                    </td>
                  </tr>

                  <tr className="border-b border-slate-300 dark:border-slate-700">
                    <th className="bg-slate-50 dark:bg-slate-800/60 p-3 font-bold border-r border-slate-300 dark:border-slate-700">
                      Assigned Department
                    </th>
                    <td className="p-3 font-semibold border-r border-slate-300 dark:border-slate-700">
                      {analysisStatus?.result?.category === 'drainage_sewage' 
                        ? 'Drainage & Sewerage Board' 
                        : analysisStatus?.result?.category === 'garbage_sanitation'
                        ? 'Solid Waste Management Division'
                        : 'Public Works Department (Roads)'}
                    </td>
                    <th className="bg-slate-50 dark:bg-slate-800/60 p-3 font-bold border-r border-slate-300 dark:border-slate-700">
                      Category Identified
                    </th>
                    <td className="p-3 font-semibold">
                      {analysisStatus?.result?.category ? (
                        <span className="capitalize">{analysisStatus.result.category.replace('_', ' & ')}</span>
                      ) : (
                        <span className="text-amber-600">Pending AI Classification...</span>
                      )}
                    </td>
                  </tr>

                  <tr className="border-b border-slate-300 dark:border-slate-700">
                    <th className="bg-slate-50 dark:bg-slate-800/60 p-3 font-bold border-r border-slate-300 dark:border-slate-700">
                      Grievance Location
                    </th>
                    <td className="p-3 border-r border-slate-300 dark:border-slate-700">
                      {complaint.location_text || 'Coordinates on file'}
                    </td>
                    <th className="bg-slate-50 dark:bg-slate-800/60 p-3 font-bold border-r border-slate-300 dark:border-slate-700">
                      Target Resolution (SLA)
                    </th>
                    <td className="p-3 font-bold text-amber-700 dark:text-amber-400">
                      Within 24 Hours (Active SLA Clock)
                    </td>
                  </tr>
                </tbody>
              </table>

              {complaint.description && (
                <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-800/40 border border-slate-300 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300">
                  <strong className="text-slate-900 dark:text-slate-100">Citizen Narrative: </strong>
                  {complaint.description}
                </div>
              )}
            </div>
          </div>

          {/* AI Analysis Findings Card (Agent 1 Intelligence) */}
          {analysisStatus?.result && (
            <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 shadow-sm transition-colors">
              <div className="bg-slate-100 dark:bg-slate-800 px-6 py-2.5 border-b border-slate-300 dark:border-slate-700 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
                  <h3 className="text-xs font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">
                    Agent 1 (AI Complaint Analyst) Assessment Findings
                  </h3>
                </div>
                <span className="text-[11px] font-mono text-slate-500">
                  Confidence: {analysisStatus.result.confidence_level.toUpperCase()}
                </span>
              </div>

              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-3 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
                    <span className="text-[11px] text-slate-500 uppercase font-semibold block">Severity Recommendation</span>
                    <span className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase mt-0.5 block">
                      {analysisStatus.result.severity_recommendation || 'Standard'}
                    </span>
                  </div>
                  <div className="p-3 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
                    <span className="text-[11px] text-slate-500 uppercase font-semibold block">Priority Score</span>
                    <span className="text-xs font-bold text-slate-900 dark:text-slate-100 mt-0.5 block">
                      {analysisStatus.result.priority_score ?? 85} / 100
                    </span>
                  </div>
                  <div className="p-3 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
                    <span className="text-[11px] text-slate-500 uppercase font-semibold block">Human Review Flag</span>
                    <span className="text-xs font-bold mt-0.5 block">
                      {analysisStatus.result.human_review_recommended ? (
                        <span className="text-rose-600 font-bold">Review Required</span>
                      ) : (
                        <span className="text-emerald-600 font-bold">Auto-Validated</span>
                      )}
                    </span>
                  </div>
                </div>

                {analysisStatus.result.visible_evidence?.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide">
                      Evidence Detected in Photograph:
                    </span>
                    <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-1 list-disc list-inside">
                      {analysisStatus.result.visible_evidence.map((ev, i) => (
                        <li key={i}>{ev}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Action Taken Report (ATR) / Audit History Table */}
          <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 shadow-sm transition-colors">
            <div className="bg-slate-100 dark:bg-slate-800 px-6 py-3 border-b border-slate-300 dark:border-slate-700 flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">
                Action Taken Report (ATR) / Official Audit Trail
              </h3>
              <span className="text-xs text-slate-500 font-medium">Real-time status updates</span>
            </div>

            <div className="p-6 overflow-x-auto">
              <table className="w-full text-xs border border-slate-300 dark:border-slate-700 text-left">
                <thead className="bg-slate-100 dark:bg-slate-800 font-bold border-b border-slate-300 dark:border-slate-700">
                  <tr>
                    <th className="p-3 border-r border-slate-300 dark:border-slate-700 w-14 text-center">S.No</th>
                    <th className="p-3 border-r border-slate-300 dark:border-slate-700 w-48">Date & Time</th>
                    <th className="p-3 border-r border-slate-300 dark:border-slate-700">Action Taken / Remarks</th>
                    <th className="p-3 w-36 text-center">Stage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-300 dark:divide-slate-700">
                  {events.length > 0 ? (
                    events.map((evt, idx) => (
                      <tr key={idx}>
                        <td className="p-3 border-r border-slate-300 dark:border-slate-700 text-center font-medium">
                          {idx + 1}
                        </td>
                        <td className="p-3 border-r border-slate-300 dark:border-slate-700 font-mono text-[11px]">
                          {new Date(evt.occurred_at).toLocaleString()}
                        </td>
                        <td className="p-3 border-r border-slate-300 dark:border-slate-700">
                          {evt.event_type}
                        </td>
                        <td className="p-3 text-center font-bold text-slate-700 dark:text-slate-300">
                          Stage {idx + 1}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="p-6 text-center text-slate-500">
                        No audit events recorded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Citizen Resolution Verification Strip */}
            <div className="bg-amber-50 dark:bg-amber-950/30 border-t border-amber-300 dark:border-amber-800 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="text-xs text-amber-950 dark:text-amber-200">
                <p className="font-bold">Citizen Resolution Verification Notice:</p>
                <p className="mt-0.5">
                  When work is completed by the department, you have 48 hours to inspect and either confirm resolution or lodge an independent dispute.
                </p>
              </div>
              <div className="flex gap-3 shrink-0">
                <button
                  type="button"
                  onClick={() => setConfirmedClosed(true)}
                  disabled={confirmedClosed}
                  className="px-5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs uppercase shadow-sm transition disabled:opacity-50"
                >
                  {confirmedClosed ? '✓ Confirmed Resolved' : 'Confirm Resolution'}
                </button>
                <button
                  type="button"
                  onClick={() => setDisputed(true)}
                  disabled={disputed}
                  className="px-5 py-2 bg-white dark:bg-slate-800 border border-slate-400 dark:border-slate-600 text-slate-800 dark:text-slate-200 font-bold text-xs uppercase shadow-sm transition disabled:opacity-50"
                >
                  {disputed ? 'Dispute Lodged' : 'Lodge Dispute'}
                </button>
              </div>
            </div>

          </div>
        </>
      )}

    </div>
  );
};
