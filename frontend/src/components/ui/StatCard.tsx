import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  color?: 'indigo' | 'yellow' | 'green' | 'red' | 'gray' | 'primary';
}

const colorMap: Record<NonNullable<StatCardProps['color']>, { iconBg: string; iconText: string; accent: string }> = {
  indigo: { iconBg: 'bg-blue-50', iconText: 'text-blue-700', accent: 'border-l-blue-500' },
  primary: { iconBg: 'bg-blue-50', iconText: 'text-blue-700', accent: 'border-l-blue-500' },
  yellow: { iconBg: 'bg-amber-50', iconText: 'text-amber-700', accent: 'border-l-amber-500' },
  green: { iconBg: 'bg-emerald-50', iconText: 'text-emerald-700', accent: 'border-l-emerald-500' },
  red: { iconBg: 'bg-rose-50', iconText: 'text-rose-700', accent: 'border-l-rose-500' },
  gray: { iconBg: 'bg-slate-100', iconText: 'text-slate-600', accent: 'border-l-slate-400' },
};

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, color = 'indigo' }) => {
  const style = colorMap[color];
  return (
    <article className={`flex items-center gap-4 rounded-2xl border border-l-4 border-slate-200 bg-white p-5 shadow-sm ${style.accent}`}>
      <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${style.iconBg}`}><Icon className={`h-5 w-5 ${style.iconText}`} /></div>
      <div className="min-w-0"><p className="text-xs font-semibold text-slate-500">{title}</p><p className="mt-1 text-2xl font-extrabold tracking-tight text-slate-900">{value}</p></div>
    </article>
  );
};

export default StatCard;
