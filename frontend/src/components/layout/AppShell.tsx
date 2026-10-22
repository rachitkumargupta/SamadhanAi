import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { clsx } from 'clsx';
import {
  LayoutDashboard, FileText, PlusCircle, Bell, User,
  LogOut, ChevronDown, Menu, X, Bot, Shield
} from 'lucide-react';

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
}

const citizenNav: NavItem[] = [
  { label: 'Dashboard', path: '/citizen', icon: LayoutDashboard },
  { label: 'My Complaints', path: '/citizen/complaints', icon: FileText },
  { label: 'Submit Complaint', path: '/citizen/submit', icon: PlusCircle },
];

const officerNav: NavItem[] = [
  { label: 'Dashboard', path: '/officer', icon: LayoutDashboard },
  { label: 'Assigned Complaints', path: '/officer/complaints', icon: FileText },
];

const adminNav: NavItem[] = [
  { label: 'Dashboard', path: '/admin', icon: LayoutDashboard },
  { label: 'All Complaints', path: '/admin/complaints', icon: FileText },
  { label: 'Departments', path: '/admin/departments', icon: Shield },
  { label: 'Officers', path: '/admin/officers', icon: User },
];

const navMap = { citizen: citizenNav, officer: officerNav, admin: adminNav };

const roleLabels = { citizen: 'Citizen', officer: 'Officer', admin: 'Admin' };
const roleBg = { citizen: 'bg-blue-600', officer: 'bg-violet-600', admin: 'bg-emerald-600' };

export const AppShell = ({ children }: { children: React.ReactNode }) => {
  const { user, notifications, unreadCount, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  if (!user) return null;
  const navItems = navMap[user.role];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-40 w-60 bg-slate-900 text-white flex flex-col transition-transform duration-200',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
          'lg:translate-x-0 lg:static lg:inset-auto'
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-700">
          <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-white text-base leading-tight block">Samadhan AI</span>
            <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">{roleLabels[user.role]} Portal</span>
          </div>
          <button
            className="ml-auto lg:hidden text-slate-400 hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/citizen' || item.path === '/officer' || item.path === '/admin'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                )
              }
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon className="w-4 h-4 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* User info at bottom */}
        <div className="p-4 border-t border-slate-700">
          <div className="flex items-center gap-3">
            <div className={clsx('w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold', roleBg[user.role])}>
              {user.name[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.name}</p>
              <p className="text-xs text-slate-400 truncate">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="mt-3 w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="sticky top-0 z-20 bg-white border-b border-slate-200 h-14 flex items-center px-4 gap-3">
          <button
            className="lg:hidden p-1.5 rounded-lg hover:bg-slate-100 text-slate-600"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex-1" />

          {/* Notifications */}
          <div className="relative">
            <button
              className="relative p-2 rounded-lg hover:bg-slate-100 text-slate-600 transition-colors"
              onClick={() => { setNotifOpen(!notifOpen); setUserMenuOpen(false); }}
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
              )}
            </button>
            {notifOpen && (
              <div className="absolute right-0 top-10 w-80 bg-white rounded-xl shadow-lg border border-slate-200 z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="font-semibold text-sm">Notifications</h3>
                  {unreadCount > 0 && <span className="badge bg-red-100 text-red-700">{unreadCount} new</span>}
                </div>
                <div className="max-h-72 overflow-y-auto divide-y divide-slate-100">
                  {notifications.slice(0, 5).map((n) => (
                    <div key={n.id} className={clsx('px-4 py-3 text-sm', !n.read && 'bg-blue-50/50')}>
                      <p className="font-medium text-slate-800">{n.title}</p>
                      <p className="text-slate-500 text-xs mt-0.5 line-clamp-2">{n.message}</p>
                    </div>
                  ))}
                  {notifications.length === 0 && (
                    <p className="text-center text-sm text-slate-400 py-6">No notifications</p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User menu */}
          <div className="relative">
            <button
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
              onClick={() => { setUserMenuOpen(!userMenuOpen); setNotifOpen(false); }}
            >
              <div className={clsx('w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold', roleBg[user.role])}>
                {user.name[0]}
              </div>
              <span className="text-sm font-medium text-slate-700 hidden sm:block">{user.name.split(' ')[0]}</span>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>
            {userMenuOpen && (
              <div className="absolute right-0 top-10 w-48 bg-white rounded-xl shadow-lg border border-slate-200 z-50 py-1">
                <div className="px-4 py-2 border-b border-slate-100">
                  <p className="text-sm font-medium text-slate-800">{user.name}</p>
                  <p className="text-xs text-slate-400">{roleLabels[user.role]}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-6 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
