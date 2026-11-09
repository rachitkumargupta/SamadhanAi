import React, { useRef, useState } from 'react';
import { Camera, X, AlertCircle } from 'lucide-react';

interface PhotoUploadProps {
  file: File | null;
  onFileSelect: (file: File | null) => void;
}

const MAX_BYTES = 10 * 1024 * 1024; // 10 MB

export const PhotoUpload: React.FC<PhotoUploadProps> = ({ file, onFileSelect }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const selected = files[0];

    if (!selected.type.startsWith('image/')) {
      setError('Only image files (JPG, PNG, JPEG) are permitted.');
      return;
    }

    if (selected.size > MAX_BYTES) {
      setError('Image exceeds 10 MB limit. Please choose a smaller photo.');
      return;
    }

    setError(null);
    onFileSelect(selected);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="space-y-2">
      <label className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
        3. Photographic Evidence <span className="text-red-600">*</span>
      </label>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-300 dark:border-red-800 text-red-700 dark:text-red-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {file ? (
        <div className="border border-slate-400 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/40 p-4 space-y-3">
          <div className="relative w-full h-56 bg-slate-200 dark:bg-slate-900 overflow-hidden flex items-center justify-center">
            <img 
              src={URL.createObjectURL(file)} 
              alt="Grievance Preview" 
              className="w-full h-full object-contain"
            />
            <button
              type="button"
              onClick={() => onFileSelect(null)}
              className="absolute top-2 right-2 p-1.5 bg-black/70 hover:bg-black text-white rounded-full transition"
              title="Remove photo"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
            <span className="font-medium truncate max-w-[200px]">{file.name}</span>
            <span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
          </div>
        </div>
      ) : (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed ${
            dragActive 
              ? 'border-blue-600 bg-blue-50 dark:bg-blue-950/20' 
              : 'border-slate-400 dark:border-slate-600 hover:border-blue-600 bg-slate-50 dark:bg-slate-800/40'
          } p-8 text-center cursor-pointer transition flex flex-col items-center justify-center min-h-[220px] gap-3`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
          <div className="w-12 h-12 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center">
            <Camera className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-bold text-slate-800 dark:text-slate-200">
              Upload Grievance Photograph or Snap Photo
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
              Supports JPG, JPEG, PNG (Max 10 MB)
            </p>
          </div>
          <button
            type="button"
            className="px-4 py-1.5 bg-white dark:bg-slate-800 border border-slate-400 dark:border-slate-600 text-xs font-semibold text-slate-800 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 shadow-sm"
          >
            Select from Device
          </button>
        </div>
      )}
    </div>
  );
};
