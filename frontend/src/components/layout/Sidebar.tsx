import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Activity, AudioWaveform, LayoutDashboard, ListOrdered, Settings2 } from 'lucide-react';

const navItems = [
  { name:'Overview', to:'/dashboard', icon:LayoutDashboard, end:true },
  { name:'Voice orders', to:'/voice', icon:AudioWaveform, end:false },
  { name:'All orders', to:'/orders', icon:ListOrdered, end:false },
  { name:'Settings', to:'/settings', icon:Settings2, end:false },
];

const Sidebar: React.FC = () => {
  const location = useLocation();
  return <aside className="z-20 flex w-full shrink-0 flex-col border-b border-[#e9e1d5] bg-[#fffefa] lg:sticky lg:top-0 lg:h-screen lg:w-[260px] lg:border-b-0 lg:border-r">
    <div className="flex items-center gap-3 px-5 py-5 lg:px-6 lg:py-5"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#145b46] text-white shadow-lg shadow-[#145b46]/20"><AudioWaveform className="h-5 w-5" /></div><div><p className="text-lg font-bold tracking-tight text-[#1b2b23]">BharatVoice</p><p className="text-[9px] font-semibold uppercase tracking-[.2em] text-[#7d8980]">Voice commerce</p></div></div>
    <div className="hidden px-4 pb-2 lg:block"><p className="px-3 text-[9px] font-bold uppercase tracking-[.18em] text-[#9a968b]">Workspace</p></div>
    <nav aria-label="Main navigation" className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-1 lg:flex-col lg:overflow-visible">{navItems.map(({name,to,icon:Icon,end})=><NavLink key={to} to={to} end={end} className={({isActive})=>`group flex shrink-0 items-center gap-3 rounded-lg px-3 py-2 text-[12px] font-medium transition-colors ${isActive||(!end&&to==='/orders'&&location.pathname.startsWith('/orders/'))?'bg-[#e8f0eb] text-[#145b46]':'text-[#59685f] hover:bg-[#f3f0e9] hover:text-[#1b2b23]'}`}><Icon className="h-4 w-4" />{name}</NavLink>)}</nav>
    <div className="hidden p-3 lg:block"><div className="rounded-xl border border-[#e9e1d5] bg-[#faf8f3] p-3"><div className="flex items-center gap-2 text-[11px] font-semibold text-[#26382f]"><Activity className="h-4 w-4 text-[#2d936e]" /> Built for local stores</div><p className="mt-1 text-[10px] leading-4 text-[#78847c]">Take orders naturally in Hindi, Hinglish and English.</p></div><div className="mt-3 flex items-center gap-2 border-t border-[#eee7dc] px-1 pt-3"><span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#145b46] text-[9px] font-bold text-white">BV</span><div><p className="text-[10px] font-semibold text-[#26382f]">Store workspace</p><p className="text-[9px] text-[#879087]">Owner account</p></div></div></div>
  </aside>;
};
export default Sidebar;
