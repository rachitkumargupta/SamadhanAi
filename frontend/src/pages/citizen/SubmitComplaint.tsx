import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ComplaintCategory } from '../../types';
import { categoryLabels } from '../../data/mockData';
import { Bot, CheckCircle, Upload, MapPin, AlertCircle } from 'lucide-react';

const categories = Object.entries(categoryLabels) as [ComplaintCategory, string][];

export const SubmitComplaint = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [form, setForm] = useState({
    title: '',
    description: '',
    category: '' as ComplaintCategory | '',
    address: '',
    ward: '',
    city: 'Bhopal',
    pincode: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const update = (field: string, val: string) => setForm((p) => ({ ...p, [field]: val }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    // Simulate AI processing
    await new Promise((r) => setTimeout(r, 2000));
    setSubmitting(false);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="max-w-lg mx-auto">
        <div className="card p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-9 h-9 text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Complaint Submitted!</h2>
          <p className="text-slate-500 text-sm mb-1">Your complaint has been registered successfully.</p>
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 my-4 text-left">
            <div className="flex items-center gap-2 mb-2">
              <Bot className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-semibold text-blue-800">AI Processing</span>
            </div>
            <div className="space-y-1.5 text-xs text-blue-700">
              <p>✓ Complaint ID generated: <strong>#C{Math.floor(1000 + Math.random() * 9000)}</strong></p>
              <p>✓ AI Complaint Analyst is classifying your complaint...</p>
              <p>✓ Resolution & Routing Agent will assign the right department</p>
              <p>✓ You will receive updates via SMS/email</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button className="btn-secondary flex-1" onClick={() => navigate('/citizen/complaints')}>
              My Complaints
            </button>
            <button className="btn-primary flex-1" onClick={() => { setSubmitted(false); setStep(1); setForm({ title: '', description: '', category: '', address: '', ward: '', city: 'Bhopal', pincode: '' }); }}>
              Submit Another
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-900">Submit a Complaint</h1>
        <p className="text-sm text-slate-500 mt-0.5">Our AI agents will analyze and route your complaint automatically</p>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-2 mb-6">
        {[1, 2, 3].map((s) => (
          <React.Fragment key={s}>
            <div className={`flex items-center gap-1.5 text-xs font-medium ${
              step >= s ? 'text-blue-600' : 'text-slate-400'
            }`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                step > s ? 'bg-green-500 text-white' : step === s ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-500'
              }`}>{step > s ? '✓' : s}</div>
              <span className="hidden sm:block">{['Complaint Details', 'Location', 'Review & Submit'][s - 1]}</span>
            </div>
            {s < 3 && <div className={`flex-1 h-0.5 ${step > s ? 'bg-blue-600' : 'bg-slate-200'}`} />}
          </React.Fragment>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card p-6">
          {/* Step 1 */}
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="font-semibold text-slate-900 mb-4">Complaint Details</h2>
              <div>
                <label className="label">Category *</label>
                <select
                  className="input"
                  value={form.category}
                  onChange={(e) => update('category', e.target.value)}
                  required
                >
                  <option value="">Select a category</option>
                  {categories.map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Title *</label>
                <input className="input" placeholder="Brief title of the issue" value={form.title} onChange={(e) => update('title', e.target.value)} required />
              </div>
              <div>
                <label className="label">Description *</label>
                <textarea
                  className="input resize-none"
                  rows={4}
                  placeholder="Describe the issue in detail — location, duration, impact..."
                  value={form.description}
                  onChange={(e) => update('description', e.target.value)}
                  required
                />
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex gap-2">
                <Bot className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <p className="text-xs text-blue-700">Our AI will automatically classify the severity, detect duplicates, and identify any missing information.</p>
              </div>
              <div>
                <label className="label">Attachments (optional)</label>
                <div className="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center hover:border-blue-400 transition-colors cursor-pointer">
                  <Upload className="w-7 h-7 text-slate-300 mx-auto mb-2" />
                  <p className="text-sm text-slate-400">Click to upload photos or documents</p>
                  <p className="text-xs text-slate-300 mt-1">PNG, JPG, PDF up to 10MB</p>
                </div>
              </div>
              <button type="button" className="btn-primary w-full" onClick={() => setStep(2)} disabled={!form.title || !form.description || !form.category}>
                Continue to Location
              </button>
            </div>
          )}

          {/* Step 2 */}
          {step === 2 && (
            <div className="space-y-4">
              <h2 className="font-semibold text-slate-900 mb-4">Location Details</h2>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex gap-2">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <p className="text-xs text-amber-700">Accurate location helps route your complaint to the right jurisdiction and officer.</p>
              </div>
              <div>
                <label className="label">Street Address *</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input className="input pl-9" placeholder="House/Building number, Street name" value={form.address} onChange={(e) => update('address', e.target.value)} required />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Ward</label>
                  <input className="input" placeholder="e.g. Ward 12" value={form.ward} onChange={(e) => update('ward', e.target.value)} />
                </div>
                <div>
                  <label className="label">Pincode</label>
                  <input className="input" placeholder="462001" value={form.pincode} onChange={(e) => update('pincode', e.target.value)} maxLength={6} />
                </div>
              </div>
              <div>
                <label className="label">City *</label>
                <input className="input" value={form.city} onChange={(e) => update('city', e.target.value)} required />
              </div>
              <div className="flex gap-3">
                <button type="button" className="btn-secondary flex-1" onClick={() => setStep(1)}>Back</button>
                <button type="button" className="btn-primary flex-1" onClick={() => setStep(3)} disabled={!form.address}>Review</button>
              </div>
            </div>
          )}

          {/* Step 3 */}
          {step === 3 && (
            <div className="space-y-4">
              <h2 className="font-semibold text-slate-900 mb-4">Review & Submit</h2>
              <div className="bg-slate-50 rounded-xl p-4 space-y-3">
                <div>
                  <p className="text-xs text-slate-500">Category</p>
                  <p className="text-sm font-medium text-slate-800">{categoryLabels[form.category as ComplaintCategory]}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Title</p>
                  <p className="text-sm font-medium text-slate-800">{form.title}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Description</p>
                  <p className="text-sm text-slate-700">{form.description}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Location</p>
                  <p className="text-sm font-medium text-slate-800">{form.address}, {form.ward && `${form.ward}, `}{form.city} {form.pincode}</p>
                </div>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Bot className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-semibold text-blue-800">What happens next?</span>
                </div>
                <div className="space-y-1 text-xs text-blue-700">
                  <p>1. Complaint Analyst AI will classify and prioritize your complaint</p>
                  <p>2. Resolution & Routing Agent will assign to the correct department</p>
                  <p>3. Monitoring Agent will track SLA and escalate if needed</p>
                  <p>4. You will be notified at every step</p>
                </div>
              </div>
              <div className="flex gap-3">
                <button type="button" className="btn-secondary flex-1" onClick={() => setStep(2)}>Back</button>
                <button type="submit" className="btn-primary flex-1" disabled={submitting}>
                  {submitting ? (
                    <span className="flex items-center gap-2"><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Processing...</span>
                  ) : 'Submit Complaint'}
                </button>
              </div>
            </div>
          )}
        </div>
      </form>
    </div>
  );
};
