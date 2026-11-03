import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle, ArrowRight, AudioWaveform, CheckCircle2, Clock3,
  Package, Plus, RefreshCw, ShoppingBag, Sparkles, TrendingUp,
} from 'lucide-react';
import { listOrders } from '../api/orders';
import { OrderResponse } from '../types/order';
import StatCard from '../components/ui/StatCard';
import StatusBadge from '../components/ui/StatusBadge';
import QuickActionCard from '../components/ui/QuickActionCard';

const PAGE_SIZE = 500;
const MAX_PAGES = 20;

const Dashboard: React.FC = () => {
  const [orders, setOrders] = useState<OrderResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [capped, setCapped] = useState(false);

  const fetchOrders = useCallback(async (refresh = false) => {
    refresh ? setRefreshing(true) : setLoading(true);
    setError('');
    try {
      const collected: OrderResponse[] = [];
      let skip = 0;
      let page = 0;
      while (page < MAX_PAGES) {
        const batch = await listOrders({ skip, limit: PAGE_SIZE });
        collected.push(...batch);
        page += 1;
        if (batch.length < PAGE_SIZE) break;
        skip += PAGE_SIZE;
      }
      setCapped(page === MAX_PAGES && collected.length === PAGE_SIZE * MAX_PAGES);
      setOrders(collected);
    } catch (err) {
      console.error('Dashboard order fetch failed', err);
      setError('We could not load store activity. Check your backend connection and try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { void fetchOrders(); }, [fetchOrders]);

  const total = orders.length;
  const awaiting = orders.filter((order) => ['pending', 'draft', 'awaiting_confirmation'].includes(order.status)).length;
  const confirmed = orders.filter((order) => order.status === 'confirmed').length;
  const clarification = orders.filter((order) => order.status === 'needs_clarification').length;
  const cancelled = orders.filter((order) => order.status === 'cancelled').length;
  const recent = [...orders].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)).slice(0, 5);
  const statuses = [
    { label: 'Awaiting review', count: awaiting, color: 'bg-blue-600' },
    { label: 'Confirmed', count: confirmed, color: 'bg-emerald-500' },
    { label: 'Needs clarification', count: clarification, color: 'bg-amber-500' },
    { label: 'Cancelled', count: cancelled, color: 'bg-slate-400' },
  ];

  return (
    <div className="mx-auto max-w-[1500px] space-y-7">
      <header className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700"><Sparkles className="h-3.5 w-3.5" /> Store intelligence</div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Good morning. Welcome to BharatVoice.</h1>
          <p className="mt-2 text-sm text-slate-500">Your voice-first workspace for faster, clearer kirana orders.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void fetchOrders(true)} disabled={refreshing || loading} className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} /> Refresh</button>
          <Link to="/voice" className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/20 hover:bg-blue-700"><Plus className="h-4 w-4" /> Create voice order</Link>
        </div>
      </header>

      {error && <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"><span className="flex items-center gap-2"><AlertCircle className="h-4 w-4" />{error}</span><button onClick={() => void fetchOrders()} className="font-semibold underline">Retry</button></div>}

      <section className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        <StatCard title="Total orders" value={loading ? '—' : total} icon={Package} color="indigo" />
        <StatCard title="Awaiting review" value={loading ? '—' : awaiting} icon={Clock3} color="yellow" />
        <StatCard title="Confirmed orders" value={loading ? '—' : confirmed} icon={CheckCircle2} color="green" />
        <StatCard title="Needs clarification" value={loading ? '—' : clarification} icon={AlertCircle} color="red" />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between"><div><h2 className="font-bold text-slate-900">Order status overview</h2><p className="mt-1 text-xs text-slate-500">Live distribution from saved orders</p></div><div className="rounded-lg bg-slate-100 p-2 text-slate-500"><TrendingUp className="h-4 w-4" /></div></div>
          {loading ? <div className="mt-7 space-y-5">{[1,2,3,4].map((x) => <div key={x} className="animate-pulse"><div className="mb-2 h-3 w-28 rounded bg-slate-100" /><div className="h-2 rounded-full bg-slate-100" /></div>)}</div> :
            total === 0 ? <div className="mt-7 rounded-xl border border-dashed border-slate-200 bg-slate-50 px-5 py-8 text-center"><div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><ShoppingBag className="h-6 w-6" /></div><p className="mt-3 text-sm font-semibold text-slate-800">Your first order is one conversation away</p><p className="mt-1 text-xs text-slate-500">Once you process an order, its status will appear here.</p><Link to="/voice" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-800">Create first order <ArrowRight className="h-4 w-4" /></Link></div> :
            <div className="mt-7 space-y-5">{statuses.map((item) => {
              const percent = Math.round((item.count / total) * 100);
              return <div key={item.label}><div className="mb-2 flex items-center justify-between text-sm"><span className="font-medium text-slate-700">{item.label}</span><span className="tabular-nums text-slate-500">{item.count} <span className="text-xs">({percent}%)</span></span></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${item.color} transition-all`} style={{ width: `${percent}%` }} /></div></div>;
            })}</div>}
        </div>

        <div className="overflow-hidden rounded-2xl bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-700 p-6 text-white shadow-lg shadow-blue-900/10">
          <div className="flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-100">Built for real conversations</p><h2 className="mt-3 max-w-sm text-2xl font-bold leading-tight">Let customers order in the language they speak.</h2></div><div className="rounded-xl bg-white/15 p-3"><AudioWaveform className="h-6 w-6" /></div></div>
          <p className="mt-3 max-w-sm text-sm leading-6 text-blue-100">Capture Hindi and Hinglish requests, turn them into structured grocery items, then review before confirming.</p>
          <Link to="/voice" className="mt-7 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-3 text-sm font-bold text-blue-700 shadow-sm hover:bg-blue-50">Start a voice order <ArrowRight className="h-4 w-4" /></Link>
          <div className="mt-8 grid grid-cols-3 gap-3 border-t border-white/20 pt-5">
            <div><p className="text-xl font-bold">01</p><p className="mt-1 text-[11px] text-blue-100">Capture</p></div><div><p className="text-xl font-bold">02</p><p className="mt-1 text-[11px] text-blue-100">Review</p></div><div><p className="text-xl font-bold">03</p><p className="mt-1 text-[11px] text-blue-100">Approve</p></div>
          </div>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-6 py-5"><div><h2 className="font-bold text-slate-900">Recent orders</h2><p className="mt-1 text-xs text-slate-500">The latest customer requests received by your store</p></div><Link to="/orders" className="inline-flex items-center gap-1 text-sm font-semibold text-blue-700 hover:text-blue-800">View all <ArrowRight className="h-4 w-4" /></Link></div>
        {loading ? <div className="space-y-3 p-6">{[1,2,3,4].map((x) => <div key={x} className="h-12 animate-pulse rounded-lg bg-slate-100" />)}</div> :
          recent.length === 0 ? <div className="px-6 py-9 text-center"><p className="text-sm font-semibold text-slate-800">No orders yet</p><p className="mt-1 text-xs text-slate-500">Your recent orders will appear here after the first voice request.</p></div> :
          <div className="overflow-x-auto"><table className="w-full min-w-[720px] text-left"><thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-400"><tr><th className="px-6 py-3">Order</th><th className="px-6 py-3">Customer request</th><th className="px-6 py-3">Items</th><th className="px-6 py-3">Status</th><th className="px-6 py-3">Created</th><th className="px-6 py-3 text-right"> </th></tr></thead><tbody className="divide-y divide-slate-100">{recent.map((order) => <tr key={order.id} className="transition hover:bg-slate-50/70"><td className="px-6 py-4 text-sm font-bold text-slate-900">#{order.id}</td><td className="max-w-sm truncate px-6 py-4 text-sm text-slate-600" title={order.transcript}>{order.transcript || 'No transcript'}</td><td className="px-6 py-4 text-sm text-slate-600">{order.items.length}</td><td className="px-6 py-4"><StatusBadge status={order.status} /></td><td className="whitespace-nowrap px-6 py-4 text-xs text-slate-500">{new Date(order.created_at).toLocaleString()}</td><td className="px-6 py-4 text-right"><Link to={`/orders/${order.id}`} className="text-sm font-semibold text-blue-700 hover:text-blue-800">Open</Link></td></tr>)}</tbody></table></div>}
      </section>

      {capped && <p className="text-xs text-amber-700">Dashboard totals are based on the latest {orders.length.toLocaleString()} orders. The maximum retrieval window was reached.</p>}

      <section><div className="mb-3"><h2 className="font-bold text-slate-900">Quick actions</h2><p className="mt-1 text-xs text-slate-500">Jump straight into your daily workflow.</p></div><div className="grid gap-3 md:grid-cols-3"><QuickActionCard title="Create voice order" description="Capture a customer request by voice" icon={AudioWaveform} to="/voice" /><QuickActionCard title="Review pending orders" description="Check requests awaiting approval" icon={Clock3} to="/orders" /><QuickActionCard title="Manage all orders" description="Search and manage your order history" icon={ListOrderedIcon} to="/orders" /></div></section>
    </div>
  );
};

const ListOrderedIcon = Package;
export default Dashboard;
