import React from 'react';
import { clsx } from 'clsx';
import { ComplaintStatus, SeverityLevel } from '../../types';
import { statusConfig, severityConfig } from '../../data/mockData';

interface StatusBadgeProps {
  status: ComplaintStatus;
  className?: string;
}

export const StatusBadge = ({ status, className }: StatusBadgeProps) => {
  const cfg = statusConfig[status];
  return (
    <span className={clsx('badge', cfg.bg, cfg.color, className)}>
      {cfg.label}
    </span>
  );
};

interface SeverityBadgeProps {
  severity: SeverityLevel;
  className?: string;
}

export const SeverityBadge = ({ severity, className }: SeverityBadgeProps) => {
  const cfg = severityConfig[severity];
  return (
    <span className={clsx('badge', cfg.bg, cfg.color, className)}>
      {cfg.label}
    </span>
  );
};
