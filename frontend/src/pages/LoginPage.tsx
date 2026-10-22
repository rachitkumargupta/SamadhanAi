import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Role } from '../types';
import { Bot, User, Shield, Settings, ChevronRight, Zap } from 'lucide-react';

const roles: { role: Role; label: string; desc: string; icon: React.ElementType; color: string; bg: string; path: string }[] = [
  {
    role: 'citizen',
    label: 'Citizen',
    desc: 'Submit and track your civic complaints',
    icon: User,
    color: 'text-blue-600',
    bg: 'bg-blue-50 border-blue-200 hover:border-blue-400 hover:bg-blue-100',
    path: '/citizen',
  },
  {
    role: 'officer',
    label: 'Government Officer',
    desc: 'Manage and resolve assigned complaints',
    icon: Shield,
    color: 'text-violet-600',
    bg: 'bg-violet-50 border-violet-200 hover:border-violet-400 hover:bg-violet-100',
    path: '/officer',
  },
  {
    role: 'admin',
    label: 'Admin',
    desc: 'Monitor system, departments, officers and analytics',
    icon: Settings,
    color: 'text-emerald-600',
    bg: 'bg-emerald-50 border-emerald-200 hover:border-emerald-400 hover:bg-emerald-100',
    path: '/admin',
  },
];

export const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = (role: Role, path: string) => {
    login(role);
    navigate(path);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-blue-500 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-blue-500/30">
            <Bot className="w-9 h-9 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Samadhan AI</h1>
          <p className="text-blue-300 text-sm mt-2">AI-Powered Multi-Agent Complaint Management</p>
          <div className="flex items-center justify-center gap-2 mt-3">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-xs text-slate-400">Powered by LangGraph · FastAPI · pgvector</span>
          </div>
        </div>

        {/* Role selector */}
        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-6">
          <h2 className="text-white font-semibold text-center mb-1">Select your role to continue</h2>
          <p className="text-slate-400 text-xs text-center mb-5">Demo mode — click to log in instantly</p>
          <div className="space-y-3">
            {roles.map((r) => (
              <button
                key={r.role}
                onClick={() => handleLogin(r.role, r.path)}
                className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-150 text-left ${r.bg}`}
              >
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center bg-white shadow-sm`}>
                  <r.icon className={`w-5 h-5 ${r.color}`} />
                </div>
                <div className="flex-1">
                  <p className={`font-semibold text-sm ${r.color}`}>{r.label}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{r.desc}</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-500 mt-6">
          Team KAFKA · Samadhan AI · Built for Smart Governance
        </p>
      </div>
    </div>
  );
};
