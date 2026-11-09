import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { ComplaintAnalysisReviewItem } from '../types';
import { CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';

export const OfficerReviewPage: React.FC = () => {
  const [items, setItems] = useState<ComplaintAnalysisReviewItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<ComplaintAnalysisReviewItem | null>(null);
  const [imageBlobUrl, setImageBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [department, setDepartment] = useState('Public Works Department (Roads Maintenance)');
  const [priority, setPriority] = useState('High Priority (24-Hour SLA Resolution)');
  const [directives, setDirectives] = useState('');
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = async () => {
    try {
      setLoading(true);
      const res = await api.getReviewQueue();
      setItems(res.items);
      if (res.items.length > 0) {
        selectItem(res.items[0]);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const selectItem = async (item: ComplaintAnalysisReviewItem) => {
    setSelectedItem(item);
    setActionMessage(null);
    const url = await api.getReviewImageUrl(item.public_reference);
    setImageBlobUrl(url);
  };

  const handleDispatch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem) return;
    setActionMessage(
      `Work Order for ${selectedItem.public_reference} successfully allocated to ${department}. SLA target: ${priority}.`
    );
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner */}
      <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 p-4 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">
            Municipal Officer Review & Allocation Workspace
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Review grievances flagged by Agent 1 for safety hazards or multi-departmental jurisdiction.
          </p>
        </div>
        <span className="px-3 py-1 bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300 border border-amber-300 text-xs font-mono font-bold">
          Queue Size: {items.length}
        </span>
      </div>

      {actionMessage && (
        <div className="p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {loading && items.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-700" />
          <span>Loading municipal review items...</span>
        </div>
      ) : selectedItem ? (
        <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 shadow-sm transition-colors">
          
          <div className="bg-slate-100 dark:bg-slate-800 px-6 py-3 border-b border-slate-300 dark:border-slate-700 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">
              Selected Case: <strong className="font-mono text-blue-700 dark:text-blue-400">{selectedItem.public_reference}</strong>
            </span>
            <span className="text-xs text-slate-500">
              Submitted: {new Date(selectedItem.submitted_at).toLocaleString()}
            </span>
          </div>

          <div className="p-6 md:p-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            {/* Left: Evidence & AI Findings (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
              <p className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
                Photographic Evidence
              </p>

              <div className="w-full h-72 bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-600 flex flex-col items-center justify-center overflow-hidden">
                {imageBlobUrl ? (
                  <img src={imageBlobUrl} alt="Complaint Evidence" className="w-full h-full object-contain" />
                ) : (
                  <div className="text-center p-6 text-slate-500">
                    <span className="text-4xl block mb-2">📷</span>
                    <p className="text-xs font-bold text-slate-700 dark:text-slate-300">Normalized Photographic Record</p>
                    <p className="text-[11px] text-slate-400 mt-1">1080p EXIF-stripped JPEG</p>
                  </div>
                )}
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-300 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300 space-y-1">
                <p><strong>Incident Location:</strong> {selectedItem.location_text || 'Coordinates on file'}</p>
                <p><strong>Citizen Narrative:</strong> {selectedItem.description || 'No additional narrative provided.'}</p>
              </div>

              {selectedItem.result?.human_review_reasons && selectedItem.result.human_review_reasons.length > 0 ? (
                <div className="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-300 space-y-1">
                  <p className="font-bold flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Agent 1 Flagged Reason:</span>
                  </p>
                  <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                    {selectedItem.result.human_review_reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>

            {/* Right: Allocation Controls (7 cols) */}
            <div className="lg:col-span-7 space-y-5">
              <p className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
                Work Allocation & Executive Orders
              </p>

              <form onSubmit={handleDispatch} className="space-y-4 text-xs">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    Designated Department
                  </label>
                  <select 
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-400 dark:border-slate-600 p-2.5 text-xs text-slate-900 dark:text-slate-100"
                  >
                    <option>Public Works Department (Roads Maintenance Unit)</option>
                    <option>Drainage & Sewerage Board</option>
                    <option>Municipal Solid Waste Management</option>
                    <option>Street Lighting & Electrical Division</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    Priority Classification (SLA)
                  </label>
                  <select 
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full bg-white dark:bg-slate-800 border border-slate-400 dark:border-slate-600 p-2.5 text-xs text-slate-900 dark:text-slate-100"
                  >
                    <option>High Priority (24-Hour SLA Resolution)</option>
                    <option>Standard Priority (48-Hour SLA Resolution)</option>
                    <option>Routine Maintenance (7-Day SLA Resolution)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                    Official Directives / Remarks for Field Team
                  </label>
                  <textarea 
                    rows={4}
                    value={directives}
                    onChange={(e) => setDirectives(e.target.value)}
                    placeholder="Enter specific instructions for the repair engineer and required resolution photographic proof..."
                    className="w-full bg-white dark:bg-slate-800 border border-slate-400 dark:border-slate-600 p-3 text-xs text-slate-900 dark:text-slate-100 leading-relaxed"
                  />
                </div>

                <div className="pt-3 flex gap-3">
                  <button 
                    type="submit"
                    className="px-6 py-2.5 bg-[#0b2545] hover:bg-[#134074] text-white text-xs font-bold uppercase tracking-wider shadow-sm transition"
                  >
                    Approve & Dispatch Work Order
                  </button>
                  <button 
                    type="button"
                    onClick={() => setActionMessage(`Requested additional details from citizen for ${selectedItem.public_reference}.`)}
                    className="px-5 py-2.5 bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-bold border border-slate-400 dark:border-slate-600 transition"
                  >
                    Request Additional Info
                  </button>
                </div>
              </form>
            </div>

          </div>

        </div>
      ) : (
        <div className="p-12 text-center text-xs text-slate-500 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700">
          No pending complaints currently in review queue.
        </div>
      )}

    </div>
  );
};
