import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Role, User, Notification } from '../types';
import { mockNotifications } from '../data/mockData';

interface AuthContextType {
  user: User | null;
  notifications: Notification[];
  unreadCount: number;
  login: (role: Role) => void;
  logout: () => void;
  markNotificationRead: (id: string) => void;
}

const MOCK_USERS: Record<Role, User> = {
  citizen: {
    id: 'citizen-1',
    name: 'Ramesh Sharma',
    email: 'ramesh.sharma@gmail.com',
    role: 'citizen',
    phone: '+91 98765 43210',
    avatarUrl: undefined,
  },
  officer: {
    id: 'officer-1',
    name: 'Vikram Singh',
    email: 'vikram.singh@bhopal.gov.in',
    role: 'officer',
    department: 'Roads & Infrastructure',
    avatarUrl: undefined,
  },
  admin: {
    id: 'admin-1',
    name: 'Rachit Kumar Gupta',
    email: 'rachit.gupta@bhopal.gov.in',
    role: 'admin',
    avatarUrl: undefined,
  },
};

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);

  const login = (role: Role) => {
    setUser(MOCK_USERS[role]);
  };

  const logout = () => {
    setUser(null);
  };

  const markNotificationRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <AuthContext.Provider value={{ user, notifications, unreadCount, login, logout, markNotificationRead }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
};
