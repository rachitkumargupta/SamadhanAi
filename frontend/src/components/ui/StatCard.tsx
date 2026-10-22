import React from 'react';
import { clsx } from 'clsx';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  trend?: { value: number; positive: boolean };
  className?: string;
}

export const StatCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-blue-600',
  iconBg = 'bg-blue-50',
  trend,
  className,
}: StatCardProps) => {
  return (
    <div className={clsx('card p-5 flex items-start gap-4', className)}>
      <div className={clsx('w-11 h-11 rounded-xl flex items-center justify-center shrink-0', iconBg)}>
        <Icon className={clsx('w-5 h-5', iconColor)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-slate-900 mt-0.5">{value}</p>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        {trend && (
          <p className={clsx('text-xs font-medium mt-1', trend.positive ? 'text-green-600' : 'text-red-500')}>
            {trend.positive ? '↑' : '↓'} {Math.abs(trend.value)}% vs last week
          </p>
        )}
      </div>
    </div>
  );
};
