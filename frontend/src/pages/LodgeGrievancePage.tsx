import React, { useState } from 'react';
import { PhotoUpload } from '../components/PhotoUpload';
import { LocationPicker } from '../components/LocationPicker';
import { api } from '../api/client';
import { Loader2, AlertCircle } from 'lucide-react';

interface LodgeGrievancePageProps {
  onSubmitted: (reference: string) => void;
}

export const LodgeGrievancePage: React.FC<LodgeGrievancePageProps> = ({ onSubmitted }) => {
  const [photo, setPhoto] = useState<File | null>(null);
  const [locationText, setLocationText] = useState('Ring Road, Near City Hospital Gate 2, Ward 12');
  const [description, setDescription] = useState(
    'A severe crater pothole has opened up on the main road opposite City Hospital Gate 2. Stagnant rainwater causes two-wheeler skids and traffic slowdown.'
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!photo) {
      setError('Please upload or capture a photo of the grievance.');
      return;
    }
    if (!locationText.trim()) {
      setError('Please provide the incident location.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const res = await api.submitComplaint(photo, description, locationText);
      onSubmitted(res.public_reference);
    } catch (err: any) {
      setError(err.message || 'Failed to register grievance. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setPhoto(null);
    setLocationText('');
    setDescription('');
    setError(null);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 shadow-sm transition-colors">
        
        {/* Form Title Banner */}
        <div className="bg-slate-100 dark:bg-slate-800 px-6 py-3.5 border-b border-slate-300 dark:border-slate-700 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
            Online Grievance Registration Form
          </h2>
          <span className="text-xs text-red-600 dark:text-red-400 font-semibold">* Required fields</span>
        </div>

        <form onSubmit={handleSubmit} className="p-6 md:p-8 space-y-8">
          
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-950/40 border border-red-300 dark:border-red-800 text-red-800 dark:text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            {/* Left Column: Location & Narrative Details (7 cols) */}
            <div className="lg:col-span-7 space-y-6">
              
              <LocationPicker
                locationText={locationText}
                onChange={setLocationText}
              />

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
                    2. Grievance Description
                  </label>
                  <span className="text-[11px] text-slate-500">{description.length} / 5,000 characters</span>
                </div>
                <textarea
                  rows={5}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enter detailed information regarding the civic issue, obstruction, or hazard..."
                  className="w-full bg-white dark:bg-slate-800 border border-slate-400 dark:border-slate-600 p-3 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:border-blue-700 leading-relaxed"
                />
              </div>

            </div>

            {/* Right Column: Evidence Photo & Advisory (5 cols) */}
            <div className="lg:col-span-5 space-y-6">
              
              <PhotoUpload
                file={photo}
                onFileSelect={setPhoto}
              />

              <div className="border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-4 space-y-3">
                <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                  Important Guidelines for Citizens
                </h3>
                <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-2 list-disc list-inside leading-normal">
                  <li>Please ensure the photograph clearly captures the problem and surrounding landmarks.</li>
                  <li>Our AI Engine analyzes the photo to determine priority and route it to the concerned division.</li>
                  <li>You will receive an official Registration Number to track the action taken report.</li>
                  <li>Once resolved, officers will submit work proof for your final confirmation.</li>
                </ul>
              </div>

            </div>

          </div>

          {/* Bottom Action Buttons */}
          <div className="pt-6 border-t border-slate-300 dark:border-slate-700 flex flex-col sm:flex-row items-center justify-end gap-4">
            <button
              type="button"
              onClick={handleReset}
              disabled={submitting}
              className="w-full sm:w-auto px-6 py-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-400 dark:border-slate-600 text-slate-800 dark:text-slate-200 text-xs font-bold uppercase tracking-wide transition disabled:opacity-50"
            >
              Clear Form
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="w-full sm:w-auto px-8 py-2.5 bg-[#0b2545] hover:bg-[#134074] text-white text-xs font-bold uppercase tracking-wider border border-[#06182c] shadow-md transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Registering Grievance...</span>
                </>
              ) : (
                <span>Submit Grievance Registration</span>
              )}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
};
