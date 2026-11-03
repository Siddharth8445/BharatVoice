import React from 'react';
import { CheckCircle2, CircleDashed, Clock3, AlertTriangle, XCircle } from 'lucide-react';

const statusMap: Record<string, { label: string; className: string; icon: React.ElementType }> = {
  pending: { label: 'Pending', className: 'bg-amber-50 text-amber-700 ring-amber-200', icon: Clock3 },
  draft: { label: 'Draft', className: 'bg-slate-100 text-slate-700 ring-slate-200', icon: CircleDashed },
  awaiting_confirmation: { label: 'Awaiting approval', className: 'bg-blue-50 text-blue-700 ring-blue-200', icon: Clock3 },
  needs_clarification: { label: 'Needs clarification', className: 'bg-orange-50 text-orange-700 ring-orange-200', icon: AlertTriangle },
  confirmed: { label: 'Confirmed', className: 'bg-emerald-50 text-emerald-700 ring-emerald-200', icon: CheckCircle2 },
  cancelled: { label: 'Cancelled', className: 'bg-rose-50 text-rose-700 ring-rose-200', icon: XCircle },
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const item = statusMap[status] || { label: status.replaceAll('_', ' '), className: 'bg-slate-100 text-slate-600 ring-slate-200', icon: CircleDashed };
  const Icon = item.icon;
  return <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-semibold capitalize ring-1 ring-inset ${item.className}`}><Icon className="h-3 w-3" />{item.label}</span>;
};

export default StatusBadge;
