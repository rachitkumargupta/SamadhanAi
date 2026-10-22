import React from 'react';
import { TimelineEvent } from '../../types';
import { clsx } from 'clsx';
import { Bot, User, Shield, Settings, MessageSquare } from 'lucide-react';

const actorIcons = {
  citizen: User,
  officer: Shield,
  admin: Shield,
  ai: Bot,
  system: Settings,
};

const eventColors: Record<TimelineEvent['type'], string> = {
  submitted: 'bg-blue-500',
  analyzed: 'bg-purple-500',
  assigned: 'bg-indigo-500',
  updated: 'bg-amber-500',
  escalated: 'bg-red-500',
  resolved: 'bg-green-500',
  closed: 'bg-slate-400',
  commented: 'bg-sky-500',
};

interface ComplaintTimelineProps {
  events: TimelineEvent[];
}

export const ComplaintTimeline = ({ events }: ComplaintTimelineProps) => {
  return (
    <div className="space-y-0">
      {events.map((event, idx) => {
        const Icon = actorIcons[event.actorRole] ?? MessageSquare;
        const isLast = idx === events.length - 1;
        return (
          <div key={event.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className={clsx('w-7 h-7 rounded-full flex items-center justify-center shrink-0 z-10', eventColors[event.type])}>
                <Icon className="w-3.5 h-3.5 text-white" />
              </div>
              {!isLast && <div className="w-px flex-1 bg-slate-200 my-1" />}
            </div>
            <div className={clsx('pb-4', isLast ? '' : '')}>
              <p className="text-sm text-slate-800 font-medium leading-snug">{event.message}</p>
              <p className="text-xs text-slate-400 mt-0.5">
                {event.actor} · {new Date(event.createdAt).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
