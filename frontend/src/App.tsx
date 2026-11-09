import { useState, useEffect } from 'react';
import { AuthProvider } from './context/AuthContext';
import { Header } from './components/Header';
import { LodgeGrievancePage } from './pages/LodgeGrievancePage';
import { GrievanceStatusPage } from './pages/GrievanceStatusPage';
import { OfficerReviewPage } from './pages/OfficerReviewPage';
import { GrievanceHistoryPage } from './pages/GrievanceHistoryPage';

export function AppContent() {
  const [currentTab, setCurrentTab] = useState<'lodge' | 'status' | 'history' | 'officer'>('lodge');
  const [trackedReference, setTrackedReference] = useState<string>('CMP/2026/08912');
  const [isDark, setIsDark] = useState<boolean>(false);

  useEffect(() => {
    if (document.documentElement.classList.contains('dark')) {
      setIsDark(true);
    }
  }, []);

  const toggleTheme = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    if (nextDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleComplaintSubmitted = (newReference: string) => {
    setTrackedReference(newReference);
    setCurrentTab('status');
  };

  const handleSelectFromHistory = (ref: string) => {
    setTrackedReference(ref);
    setCurrentTab('status');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f8fafc] dark:bg-[#0b1320] text-slate-900 dark:text-slate-100 transition-colors duration-150 antialiased">
      <Header
        currentTab={currentTab}
        onTabChange={(tab) => setCurrentTab(tab as any)}
        isDark={isDark}
        onToggleTheme={toggleTheme}
      />

      <main className="max-w-7xl w-full mx-auto px-6 py-8 flex-1">
        {currentTab === 'lodge' && (
          <LodgeGrievancePage onSubmitted={handleComplaintSubmitted} />
        )}

        {currentTab === 'status' && (
          <GrievanceStatusPage initialReference={trackedReference} />
        )}

        {currentTab === 'history' && (
          <GrievanceHistoryPage onSelectComplaint={handleSelectFromHistory} />
        )}

        {currentTab === 'officer' && (
          <OfficerReviewPage />
        )}
      </main>

      <footer className="bg-slate-200 dark:bg-slate-900 border-t border-slate-300 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400 py-6 px-6 transition-colors">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <strong>Samadhan AI</strong> • Municipal Public Grievance Redressal System • Hosted by Municipal Data Center
          </div>
          <div className="flex gap-4">
            <a href="#guidelines" className="hover:underline">Portal Guidelines</a>
            <a href="#privacy" className="hover:underline">Privacy Policy</a>
            <a href="#terms" className="hover:underline">Terms of Service</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
