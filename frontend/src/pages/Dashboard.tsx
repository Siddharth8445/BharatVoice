import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, ArrowRight, AudioWaveform, CheckCircle2, Clock3, Package, RefreshCw, ShoppingBag } from 'lucide-react';
import { listOrders } from '../api/orders';
import { OrderResponse } from '../types/order';
import StatusBadge from '../components/ui/StatusBadge';

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
    } finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { void fetchOrders(); }, [fetchOrders]);

  const total = orders.length;
  const awaiting = orders.filter(o => ['pending', 'draft', 'awaiting_confirmation'].includes(o.status)).length;
  const confirmed = orders.filter(o => o.status === 'confirmed').length;
  const clarification = orders.filter(o => o.status === 'needs_clarification').length;
  const cancelled = orders.filter(o => o.status === 'cancelled').length;
  const recent = useMemo(() => [...orders].sort((a,b) => Date.parse(b.created_at)-Date.parse(a.created_at)).slice(0,6), [orders]);
  const percent = (n: number) => total ? Math.round(n / total * 100) : 0;
  const a1 = total ? awaiting / total * 360 : 0;
  const a2 = a1 + (total ? confirmed / total * 360 : 0);
  const a3 = a2 + (total ? clarification / total * 360 : 0);
  const dateLabel = new Intl.DateTimeFormat('en-IN', { weekday:'long', day:'numeric', month:'long' }).format(new Date());
  const statuses = [
    { label:'Awaiting review', count:awaiting, color:'#596db5' },
    { label:'Confirmed', count:confirmed, color:'#2d936e' },
    { label:'Needs clarification', count:clarification, color:'#cf8a12' },
    { label:'Cancelled', count:cancelled, color:'#cfc7b8' },
  ];
  const cards = [
    { title:'Total orders', value:total, icon:Package, color:'#145b46', bg:'#e8f0eb', bar:'#145b46', share:100, note:'All saved orders' },
    { title:'Awaiting review', value:awaiting, icon:Clock3, color:'#596db5', bg:'#edf0fa', bar:'#596db5', share:percent(awaiting), note:percent(awaiting)+'% of orders' },
    { title:'Confirmed orders', value:confirmed, icon:CheckCircle2, color:'#2d936e', bg:'#e5f2eb', bar:'#2d936e', share:percent(confirmed), note:percent(confirmed)+'% of orders' },
    { title:'Needs clarification', value:clarification, icon:AlertCircle, color:'#c98512', bg:'#fbf0dc', bar:'#c98512', share:percent(clarification), note:percent(clarification)+'% of orders' },
  ];

  return <div className="dashboard-page mx-auto max-w-[1500px] space-y-5">
    <header className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
      <div>
        <div className="mb-3 inline-flex items-center gap-2 text-[11px] font-medium tracking-wide text-[#64756d]"><span className="h-2 w-2 rounded-full bg-[#2d936e] ring-4 ring-[#dcece3]" />{dateLabel} · Live from your store</div>
        <h1 className="dashboard-display text-[42px] leading-[1.03] tracking-[-0.045em] text-[#17251f] sm:text-[48px]">Good morning.<span className="block text-[#145b46]">Orders, in every <span className="text-[#b58b39]">language.</span></span></h1>
        <p className="mt-3 text-[13px] text-[#718078]">Your voice-first workspace for faster, clearer kirana orders.</p>
      </div>
      <div className="flex shrink-0 flex-wrap gap-2">
        <button onClick={() => void fetchOrders(true)} disabled={refreshing || loading} className="inline-flex items-center gap-2 rounded-xl border border-[#e8dfd1] bg-white px-4 py-2.5 text-xs font-semibold text-[#263b32] shadow-sm hover:bg-[#f8f5ef] disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} /> Refresh</button>
        <Link to="/voice" className="inline-flex items-center gap-2 rounded-xl bg-[#145b46] px-4 py-2.5 text-xs font-semibold text-white shadow-lg shadow-[#145b46]/15 hover:bg-[#0b3d30]"><AudioWaveform className="h-4 w-4" /> Create voice order</Link>
      </div>
    </header>

    {error && <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"><span className="flex items-center gap-2"><AlertCircle className="h-4 w-4" />{error}</span><button onClick={() => void fetchOrders()} className="font-semibold underline">Retry</button></div>}

    <section className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-4">
      {cards.map(({title,value,icon:Icon,color,bg,bar,share,note}) => <article key={title} className="rounded-2xl border border-[#e9e1d5] bg-[#fffefa] p-4 shadow-[0_2px_8px_rgba(43,37,25,.025)]">
        <div className="flex items-center justify-between"><p className="text-[11px] font-medium text-[#68766f]">{title}</p><span className="flex h-8 w-8 items-center justify-center rounded-lg" style={{backgroundColor:bg,color}}><Icon className="h-4 w-4" /></span></div>
        <p className="mt-3 text-[30px] font-semibold leading-none tracking-tight text-[#18251f]">{loading?'—':value}</p>
        <div className="mt-3 flex items-center gap-2"><div className="h-[3px] flex-1 overflow-hidden rounded-full bg-[#eee8dd]"><div className="h-full rounded-full" style={{width:`${loading?0:share}%`,backgroundColor:bar}} /></div><span className="whitespace-nowrap text-[9px] text-[#829087]">{loading?'Loading…':note}</span></div>
      </article>)}
    </section>

    <section className="grid gap-3 xl:grid-cols-[1.02fr_.98fr]">
      <article className="min-h-[300px] rounded-2xl border border-[#e9e1d5] bg-[#fffefa] p-5 shadow-[0_2px_8px_rgba(43,37,25,.025)] sm:p-6">
        <div className="flex items-start justify-between"><div><h2 className="text-[13px] font-bold text-[#1b2b23]">Order status overview</h2><p className="mt-1 text-[11px] text-[#7b877f]">Live distribution from saved orders</p></div><span className="rounded-lg bg-[#f2eee5] px-3 py-1.5 text-[10px] font-semibold text-[#52645a]">All time</span></div>
        {loading ? <div className="mt-8 h-40 animate-pulse rounded-xl bg-[#f2eee8]" /> : total===0 ? <div className="mt-7 rounded-xl border border-dashed border-[#e5ddcf] bg-[#faf8f3] px-5 py-8 text-center"><ShoppingBag className="mx-auto h-9 w-9 text-[#145b46]" /><p className="mt-3 text-sm font-semibold text-[#26382f]">Your first order is one conversation away</p><p className="mt-1 text-xs text-[#78847c]">Once you process an order, its status will appear here.</p><Link to="/voice" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[#145b46]">Create first order <ArrowRight className="h-4 w-4" /></Link></div> :
        <div className="mt-6 flex flex-col items-center gap-7 sm:flex-row sm:justify-around">
          <div className="relative h-[158px] w-[158px] shrink-0 rounded-full" style={{background:`conic-gradient(#596db5 0deg ${a1}deg,#2d936e ${a1}deg ${a2}deg,#cf8a12 ${a2}deg ${a3}deg,#cfc7b8 ${a3}deg 360deg)`}}><div className="absolute inset-[15px] flex flex-col items-center justify-center rounded-full bg-[#fffefa]"><span className="text-[28px] font-semibold leading-none text-[#17251f]">{total}</span><span className="mt-1 text-[10px] text-[#879087]">orders</span></div></div>
          <div className="w-full max-w-[310px] space-y-3">{statuses.map(s=><div key={s.label}><div className="mb-1 flex items-center justify-between gap-3 text-[11px]"><span className="flex items-center gap-2 font-medium text-[#26382f]"><span className="h-2 w-2 rounded-full" style={{backgroundColor:s.color}} />{s.label}</span><span className="font-semibold text-[#26382f]">{s.count} <span className="font-normal text-[#859087]">{percent(s.count)}%</span></span></div><div className="h-[4px] overflow-hidden rounded-full bg-[#eee8dd]"><div className="h-full rounded-full" style={{width:`${percent(s.count)}%`,backgroundColor:s.color}} /></div></div>)}</div>
        </div>}
      </article>

      <article className="relative isolate flex min-h-[300px] flex-col overflow-hidden rounded-2xl bg-[#0b3d30] p-6 text-white shadow-[0_12px_28px_rgba(11,61,48,.12)]">
        <div className="absolute inset-0 -z-10 opacity-30" style={{backgroundImage:'linear-gradient(rgba(255,255,255,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.07) 1px,transparent 1px)',backgroundSize:'28px 28px'}} /><div className="absolute -right-10 -top-16 -z-10 h-56 w-56 rounded-full bg-[#c4a45c]/20 blur-3xl" />
        <p className="text-[9px] font-bold uppercase tracking-[.22em] text-[#d9bd79]">Built for real conversations</p>
        <h2 className="dashboard-display mt-3 max-w-[390px] text-[30px] leading-[1.08] tracking-[-.025em] text-[#fffaf0]">Let customers order in the language they speak.</h2>
        <p className="mt-3 max-w-[390px] text-[11px] leading-[1.7] text-[#c6d9d0]">Capture Hindi and Hinglish requests, transform conversations into structured grocery orders, and review them before confirmation.</p>
        <div className="my-5 flex h-10 items-center gap-[3px] text-[#c5a45e]" aria-hidden="true">{Array.from({length:42},(_,i)=><span key={i} className="w-[3px] rounded-full bg-current" style={{height:`${8+Math.abs(Math.sin(i*1.7)*Math.cos(i*.31))*30}px`}} />)}</div>
        <div className="flex flex-wrap gap-2 text-[9px] font-semibold"><span className="rounded-full bg-[#f2e7c8] px-3 py-1.5 text-[#174b3c]">हिन्दी</span><span className="rounded-full border border-white/25 bg-white/10 px-3 py-1.5">Hinglish</span><span className="rounded-full border border-white/25 bg-white/10 px-3 py-1.5">English</span></div>
        <Link to="/voice" className="mt-4 inline-flex w-fit items-center gap-2 rounded-lg bg-[#f2e7c8] px-4 py-2.5 text-[11px] font-bold text-[#164b3b] hover:bg-white">Start a voice order <ArrowRight className="h-4 w-4" /></Link>
        <div className="mt-auto grid grid-cols-3 gap-2 border-t border-white/15 pt-4 text-[10px] font-semibold text-[#e5eee9]">{['Capture','Review','Approve'].map((label,i)=><div key={label} className="flex items-center gap-2"><span className="rounded bg-white/15 px-1.5 py-1 text-[9px] text-[#f2e7c8]">0{i+1}</span>{label}</div>)}</div>
      </article>
    </section>

    <section className="overflow-hidden rounded-2xl border border-[#e9e1d5] bg-[#fffefa] shadow-[0_2px_8px_rgba(43,37,25,.025)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#eee7dc] px-5 py-4 sm:px-6"><div><h2 className="text-[13px] font-bold text-[#1b2b23]">Recent orders</h2><p className="mt-1 text-[10px] text-[#7b877f]">Latest voice orders captured in your store</p></div><Link to="/orders" className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#145b46]">View all orders <ArrowRight className="h-3.5 w-3.5" /></Link></div>
      {loading ? <div className="space-y-3 p-6">{[1,2,3,4].map(x=><div key={x} className="h-12 animate-pulse rounded-lg bg-[#f2eee8]" />)}</div> : recent.length===0 ? <div className="px-6 py-10 text-center"><p className="text-sm font-semibold text-[#26382f]">No orders yet</p><p className="mt-1 text-xs text-[#7b877f]">Your recent orders will appear here after the first voice request.</p></div> :
      <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left"><thead className="bg-[#faf7f1] text-[9px] font-bold uppercase tracking-[.12em] text-[#9a968b]"><tr><th className="px-5 py-3">Order ID</th><th className="px-5 py-3">Customer request</th><th className="px-5 py-3">Items</th><th className="px-5 py-3">Status</th><th className="px-5 py-3">Date</th><th className="px-5 py-3 text-right"></th></tr></thead><tbody className="divide-y divide-[#f0eadf]">{recent.map(order=><tr key={order.id} className="transition hover:bg-[#faf8f3]"><td className="px-5 py-3.5 text-[11px] font-bold text-[#1c3027]">#{order.id}</td><td className="max-w-[300px] truncate px-5 py-3.5 text-[11px] text-[#59685f]" title={order.transcript}>{order.transcript||'No transcript'}</td><td className="px-5 py-3.5 text-[11px] text-[#59685f]">{order.items.length} {order.items.length===1?'item':'items'}</td><td className="px-5 py-3.5"><StatusBadge status={order.status} /></td><td className="whitespace-nowrap px-5 py-3.5 text-[10px] text-[#718078]">{new Date(order.created_at).toLocaleTimeString('en-IN',{hour:'numeric',minute:'2-digit'})} · {new Date(order.created_at).toLocaleDateString('en-IN',{day:'numeric',month:'short'})}</td><td className="px-5 py-3.5 text-right"><Link to={`/orders/${order.id}`} className="inline-flex items-center gap-1 rounded-lg border border-[#e8dfd1] px-3 py-1.5 text-[10px] font-semibold text-[#145b46] hover:bg-[#edf3ee]"><Package className="h-3 w-3" /> View</Link></td></tr>)}</tbody></table></div>}
      <div className="flex items-center justify-between border-t border-[#eee7dc] px-5 py-3.5 text-[10px] text-[#7b877f]"><span>Showing 1–{recent.length} of {total} orders</span><Link to="/orders" className="inline-flex items-center gap-1 font-semibold text-[#145b46]">Open order history <ArrowRight className="h-3 w-3" /></Link></div>
    </section>
    {capped && <p className="text-xs text-amber-700">Dashboard totals are based on the latest {orders.length.toLocaleString()} orders. The maximum retrieval window was reached.</p>}
  </div>;
};

export default Dashboard;
