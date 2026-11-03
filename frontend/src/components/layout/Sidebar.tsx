import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Activity, AudioWaveform, LayoutDashboard, ListOrdered, Settings2, Store } from 'lucide-react';

const navItems = [
  { name: 'Overview', to: '/dashboard', icon: LayoutDashboard, end: true },
  { name: 'Voice orders', to: '/voice', icon: AudioWaveform, end: false },
  { name: 'All orders', to: '/orders', icon: ListOrdered, end: false },
  { name: 'Settings', to: '/settings', icon: Settings2, end: false },
];

const Sidebar: React.FC = () => {
  const location = useLocation();
  return (
    <aside className="z-20 flex w-full shrink-0 flex-col border-b border-slate-200 bg-white lg:sticky lg:top-0 lg:h-screen lg:w-[260px] lg:border-b-0 lg:border-r">
      <div className="flex items-center gap-3 px-5 py-5 lg:px-6 lg:py-7">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-600/20"><Store className="h-5 w-5" /></div>
        <div><p className="text-lg font-bold tracking-tight text-slate-900">BharatVoice</p><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Voice commerce</p></div>
      </div>
      <div className="hidden px-4 pb-3 lg:block"><p className="px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Workspace</p></div>
      <nav aria-label="Main navigation" className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-1 lg:flex-col lg:overflow-visible lg:px-4">
        {navItems.map(({ name, to, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) =>
            `group flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${isActive || (!end && to === '/orders' && location.pathname.startsWith('/orders/')) ? 'bg-blue-600 text-white shadow-md shadow-blue-600/15' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`
          }>
            <Icon className="h-[18px] w-[18px]" />{name}
          </NavLink>
        ))}
      </nav>
      <div className="hidden p-4 lg:block">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700"><Activity className="h-4 w-4 text-emerald-600" /> Built for local stores</div>
          <p className="mt-2 text-xs leading-5 text-slate-500">Take orders naturally in Hindi, Hinglish and English.</p>
        </div>
        <p className="mt-4 px-1 text-[10px] text-slate-400">BHARATVOICE · DEVELOPMENT</p>
      </div>
    </aside>
  );
};

export default Sidebar;
