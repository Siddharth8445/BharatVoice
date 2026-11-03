import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ChevronLeft, ChevronRight, Filter, ListFilter, RefreshCw, Search, ShoppingBag } from 'lucide-react';
import { listOrders } from '../api/orders';
import { OrderResponse } from '../types/order';
import StatusBadge from '../components/ui/StatusBadge';

const PAGE_SIZE = 50;
const getMessage = (error: unknown) => {
  const value = error as { response?: { data?: { detail?: string } }; message?: string };
  return value.response?.data?.detail || value.message || 'Unable to load orders. Check the backend connection.';
};

const Orders: React.FC = () => {
  const [orders, setOrders] = useState<OrderResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listOrders({
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
        ...(statusFilter ? { status_filter: statusFilter } : {}),
      });
      setOrders(data);
      setHasNext(data.length === PAGE_SIZE);
    } catch (err) {
      setError(getMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => { void fetchOrders(); }, [fetchOrders]);

  const filtered = useMemo(() => {
    const term = search.trim().toLocaleLowerCase();
    if (!term) return orders;
    return orders.filter((order) =>
      String(order.id).includes(term) || order.transcript.toLocaleLowerCase().includes(term) ||
      order.items.some((item) => item.product_name.toLocaleLowerCase().includes(term))
    );
  }, [orders, search]);

  const changeFilter = (value: string) => { setStatusFilter(value); setPage(1); };

  return (
    <div className="mx-auto max-w-[1500px] space-y-7">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">Order management</p><h1 className="mt-2 text-3xl font-extrabold tracking-tight text-slate-900">All orders</h1><p className="mt-2 text-sm text-slate-500">Search, review and manage customer orders from one place.</p></div>
        <Link to="/voice" className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/20 hover:bg-blue-700"><ShoppingBag className="h-4 w-4" /> Create voice order</Link>
      </header>

      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative min-w-0 flex-1 lg:max-w-md"><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search order ID, transcript or product…" className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /></div>
          <div className="flex flex-wrap items-center gap-2"><div className="flex items-center gap-2 text-xs font-semibold text-slate-500"><Filter className="h-4 w-4" /> Status</div><select value={statusFilter} onChange={(event) => changeFilter(event.target.value)} className="min-w-[190px] rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none focus:border-blue-400"><option value="">All statuses</option><option value="awaiting_confirmation">Awaiting approval</option><option value="needs_clarification">Needs clarification</option><option value="confirmed">Confirmed</option><option value="cancelled">Cancelled</option></select><button onClick={() => void fetchOrders()} disabled={loading} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh</button></div>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 sm:px-6"><div><h2 className="font-bold text-slate-900">Order records</h2><p className="mt-1 text-xs text-slate-500">{loading ? 'Loading records…' : `${filtered.length} shown on this page`}</p></div><div className="rounded-lg bg-slate-100 p-2 text-slate-500"><ListFilter className="h-4 w-4" /></div></div>
        {error && <div role="alert" className="m-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}<button onClick={() => void fetchOrders()} className="ml-2 font-bold underline">Retry</button></div>}
        {loading ? <div className="space-y-3 p-6">{[1,2,3,4,5].map((item) => <div key={item} className="h-12 animate-pulse rounded-lg bg-slate-100" />)}</div> :
          filtered.length === 0 ? <div className="px-6 py-16 text-center"><div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400"><ShoppingBag className="h-6 w-6" /></div><h3 className="mt-4 font-semibold text-slate-900">{orders.length === 0 ? 'No orders found yet' : 'No matching orders'}</h3><p className="mt-1 text-sm text-slate-500">{orders.length === 0 ? 'Your first voice order will appear here.' : 'Try another search term or clear the status filter.'}</p>{orders.length === 0 && <Link to="/voice" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-blue-700">Create first order <ArrowRight className="h-4 w-4" /></Link>}</div> :
          <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left"><thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-400"><tr><th className="px-6 py-3">Order ID</th><th className="px-6 py-3">Customer request</th><th className="px-6 py-3">Items</th><th className="px-6 py-3">Status</th><th className="px-6 py-3">Created</th><th className="px-6 py-3 text-right">Action</th></tr></thead><tbody className="divide-y divide-slate-100">{filtered.map((order) => <tr key={order.id} className="hover:bg-slate-50/70"><td className="px-6 py-4 text-sm font-bold text-slate-900">#{order.id}</td><td className="max-w-sm truncate px-6 py-4 text-sm text-slate-600" title={order.transcript}>{order.transcript || '—'}</td><td className="px-6 py-4 text-sm text-slate-600">{order.items.length}</td><td className="px-6 py-4"><StatusBadge status={order.status} /></td><td className="whitespace-nowrap px-6 py-4 text-xs text-slate-500">{new Date(order.created_at).toLocaleString()}</td><td className="px-6 py-4 text-right"><Link to={`/orders/${order.id}`} className="text-sm font-semibold text-blue-700 hover:text-blue-800">View details</Link></td></tr>)}</tbody></table></div>}
        <div className="flex items-center justify-between border-t border-slate-100 px-5 py-4 sm:px-6"><p className="text-xs text-slate-500">Page {page} · {PAGE_SIZE} records per request</p><div className="flex gap-2"><button onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1 || loading} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40"><ChevronLeft className="h-4 w-4" /> Previous</button><button onClick={() => setPage((current) => current + 1)} disabled={!hasNext || loading} className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40">Next <ChevronRight className="h-4 w-4" /></button></div></div>
      </section>
      <p className="text-xs text-slate-400">Search is applied to the currently loaded page. Status filtering and pagination are handled by the backend.</p>
    </div>
  );
};

export default Orders;
