import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { ChevronRight, Store } from 'lucide-react';
import Sidebar from './Sidebar';

const pageNames: Record<string,string> = {'/dashboard':'Overview','/voice':'Voice orders','/orders':'All orders','/settings':'Settings'};
const Layout: React.FC = () => {
  const location = useLocation();
  const title = location.pathname.startsWith('/orders/') ? 'Order details' : pageNames[location.pathname] || 'Workspace';
  return <div className="min-h-screen bg-[#f7f4ee] text-[#26382f] lg:flex">
    <Sidebar />
    <div className="min-w-0 flex-1">
      <header className="sticky top-0 z-10 hidden h-[54px] items-center justify-between border-b border-[#e9e1d5] bg-[#fffefa]/95 px-7 backdrop-blur lg:flex">
        <div className="flex items-center gap-2 text-[11px] text-[#9a968b]"><span>Workspace</span><ChevronRight className="h-3 w-3" /><span className="font-semibold text-[#26382f]">{title}</span></div>
        <div className="flex items-center gap-3"><div className="flex items-center gap-2 rounded-lg border border-[#e9e1d5] bg-white px-3 py-1.5 text-[10px] font-medium text-[#405249]"><Store className="h-3.5 w-3.5" /> Store workspace</div><div className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#e9e1d5] bg-white text-[11px] text-[#145b46]">●</div></div>
      </header>
      <main className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-6"><Outlet /></main>
    </div>
  </div>;
};
export default Layout;
