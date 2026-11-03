import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { ChevronRight, Store } from 'lucide-react';
import Sidebar from './Sidebar';

const pageNames: Record<string, string> = {
  '/dashboard': 'Overview',
  '/voice': 'Voice orders',
  '/orders': 'All orders',
  '/settings': 'Settings',
};

const Layout: React.FC = () => {
  const location = useLocation();
  const title = location.pathname.startsWith('/orders/') ? 'Order details' : pageNames[location.pathname] || 'Workspace';

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 lg:flex">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-10 hidden h-[68px] items-center justify-between border-b border-slate-200/80 bg-white/90 px-8 backdrop-blur lg:flex">
          <div className="flex items-center gap-2 text-sm text-slate-400"><span>Workspace</span><ChevronRight className="h-3.5 w-3.5" /><span className="font-semibold text-slate-800">{title}</span></div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">Store workspace</div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-700"><Store className="h-4 w-4" /></div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
