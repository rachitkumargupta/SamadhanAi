import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Moon, Sun, Database, CheckCircle } from 'lucide-react';

interface HeaderProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  isDark: boolean;
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onTabChange,
  isDark,
  onToggleTheme,
}) => {
  const { role, switchRole, isMockMode, toggleMockMode } = useAuth();

  return (
    <>
      {/* Top Official Accessibility & Status Bar */}
      <div className="bg-slate-100 dark:bg-slate-900 border-b border-slate-300 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400 px-6 py-1.5 transition-colors">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-800 dark:text-slate-200">CIVIC GRIEVANCE REDRESSAL SYSTEM</span>
            <span>•</span>
            <span>MUNICIPAL CORPORATION</span>
          </div>

          <div className="flex items-center gap-4">
            {/* Mode Indicator & Switcher */}
            <button
              onClick={toggleMockMode}
              className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-bold border transition ${
                isMockMode
                  ? 'bg-amber-100 dark:bg-amber-950/50 text-amber-900 dark:text-amber-300 border-amber-300 dark:border-amber-700'
                  : 'bg-emerald-100 dark:bg-emerald-950/50 text-emerald-900 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700'
              }`}
              title="Click to toggle between real FastAPI backend and demo mock mode"
            >
              {isMockMode ? (
                <>
                  <Database className="w-3 h-3 text-amber-600" />
                  <span>Mode: Mock Demo (Click for Live)</span>
                </>
              ) : (
                <>
                  <CheckCircle className="w-3 h-3 text-emerald-600" />
                  <span>Mode: Live API (Port 8000)</span>
                </>
              )}
            </button>

            {/* Dark / Light Mode Toggle */}
            <button
              onClick={onToggleTheme}
              className="font-semibold text-slate-700 dark:text-slate-300 hover:underline flex items-center gap-1"
              title="Toggle theme"
            >
              {isDark ? (
                <>
                  <Sun className="w-3.5 h-3.5 text-amber-400" />
                  <span>Light Mode</span>
                </>
              ) : (
                <>
                  <Moon className="w-3.5 h-3.5 text-slate-600" />
                  <span>Dark Mode</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Main Gov Header Banner */}
      <header className="bg-[#0b2545] text-white shadow-md border-b-4 border-amber-500">
        <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 border-2 border-amber-400/50 rounded bg-white/10 flex items-center justify-center font-bold text-2xl text-amber-300 shrink-0">
              🏛️
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white leading-tight">Samadhan AI</h1>
              <p className="text-xs text-slate-300 tracking-wider uppercase mt-0.5">
                Integrated Citizen Grievance Redressal & Resolution Platform
              </p>
            </div>
          </div>

          {/* Quick Role Switcher */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-300 font-medium">Switch Portal:</span>
            <button
              onClick={() => {
                switchRole('citizen');
                onTabChange('lodge');
              }}
              className={`px-3 py-1.5 font-bold rounded text-xs transition ${
                role === 'citizen'
                  ? 'bg-amber-500 text-slate-950 shadow-sm'
                  : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
              }`}
            >
              Citizen Portal
            </button>
            <button
              onClick={() => {
                switchRole('officer');
                onTabChange('officer');
              }}
              className={`px-3 py-1.5 font-bold rounded text-xs transition ${
                role === 'officer'
                  ? 'bg-amber-500 text-slate-950 shadow-sm'
                  : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
              }`}
            >
              Officer Portal
            </button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-[#134074] text-white text-xs font-semibold border-b border-slate-300 dark:border-slate-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 flex flex-wrap">
          <button
            onClick={() => onTabChange('lodge')}
            className={`px-6 py-3 border-b-2 transition ${
              currentTab === 'lodge'
                ? 'border-amber-400 bg-black/20 font-bold text-amber-300'
                : 'border-transparent hover:bg-black/10 text-white'
            }`}
          >
            Lodge Grievance
          </button>
          <button
            onClick={() => onTabChange('status')}
            className={`px-6 py-3 border-b-2 transition ${
              currentTab === 'status'
                ? 'border-amber-400 bg-black/20 font-bold text-amber-300'
                : 'border-transparent hover:bg-black/10 text-white'
            }`}
          >
            View Grievance Status
          </button>
          <button
            onClick={() => onTabChange('history')}
            className={`px-6 py-3 border-b-2 transition ${
              currentTab === 'history'
                ? 'border-amber-400 bg-black/20 font-bold text-amber-300'
                : 'border-transparent hover:bg-black/10 text-white'
            }`}
          >
            My Grievance History
          </button>
          {role === 'officer' && (
            <button
              onClick={() => onTabChange('officer')}
              className={`px-6 py-3 border-b-2 transition ${
                currentTab === 'officer'
                  ? 'border-amber-400 bg-black/20 font-bold text-amber-300'
                  : 'border-transparent hover:bg-black/10 text-white'
              }`}
            >
              Officer Review Queue
            </button>
          )}
        </div>
      </nav>
    </>
  );
};
