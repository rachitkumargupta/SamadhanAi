import React, { createContext, useContext, useState, useEffect } from 'react';
import { generateDevToken } from '../api/auth';
import { api } from '../api/client';

interface AuthContextType {
  role: 'citizen' | 'officer';
  token: string;
  isMockMode: boolean;
  backendAlive: boolean;
  switchRole: (role: 'citizen' | 'officer') => Promise<void>;
  toggleMockMode: () => void;
  checkBackend: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [role, setRole] = useState<'citizen' | 'officer'>('citizen');
  const [token, setToken] = useState<string>('');
  const [isMockMode, setIsMockMode] = useState<boolean>(false);
  const [backendAlive, setBackendAlive] = useState<boolean>(false);

  const checkBackend = async () => {
    const alive = await api.checkHealth();
    setBackendAlive(alive);
    if (!alive) {
      // Auto-fallback to mock mode if backend is not running
      setIsMockMode(true);
      api.setMockMode(true);
    }
  };

  const switchRole = async (newRole: 'citizen' | 'officer') => {
    setRole(newRole);
    const subject = newRole === 'citizen' ? 'citizen-demo-user' : 'officer-demo-reviewer';
    const newToken = await generateDevToken(subject, newRole);
    setToken(newToken);
    api.setToken(newToken);
  };

  const toggleMockMode = () => {
    const next = !isMockMode;
    setIsMockMode(next);
    api.setMockMode(next);
  };

  useEffect(() => {
    switchRole('citizen');
    checkBackend();
  }, []);

  return (
    <AuthContext.Provider value={{
      role,
      token,
      isMockMode,
      backendAlive,
      switchRole,
      toggleMockMode,
      checkBackend
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};
