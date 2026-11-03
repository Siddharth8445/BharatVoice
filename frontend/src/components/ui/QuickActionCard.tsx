import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight, LucideIcon } from 'lucide-react';

interface QuickActionCardProps {
  title: string;
  description?: string;
  icon: LucideIcon;
  to: string;
}

const QuickActionCard: React.FC<QuickActionCardProps> = ({ title, description, icon: Icon, to }) => (
  <Link to={to} className="group flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md">
    <div className="flex min-w-0 items-center gap-3">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700 transition group-hover:bg-blue-600 group-hover:text-white"><Icon className="h-5 w-5" /></div>
      <div className="min-w-0"><h3 className="text-sm font-bold text-slate-900 group-hover:text-blue-700">{title}</h3>{description && <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>}</div>
    </div>
    <ArrowUpRight className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:text-blue-600" />
  </Link>
);

export default QuickActionCard;
