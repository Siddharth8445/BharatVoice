import React, { useCallback, useEffect, useState } from 'react';
import { Activity, CheckCircle2, Clock3, Database, Globe2, RefreshCw, Server, ShieldCheck, XCircle } from 'lucide-react';
import { getHealth, HealthResponse } from '../api/health';

const Settings: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setHealth(await getHealth());
    } catch {
      setHealth(null);
      setError('Unable to reach the BharatVoice API. Check that the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const healthy = health?.status === 'healthy';
  const rows = [
    { label: 'API service', value: health?.status ?? 'Unavailable', icon: Server, ok: healthy },
    { label: 'Database', value: health?.database ?? 'Unknown', icon: Database, ok: health?.database === 'connected' },
    { label: 'AI provider mode', value: health ? (health.use_mock_gnani ? 'Mock / development' : 'Gnani live provider') : 'Unknown', icon: Activity, ok: !!health },
    { label: 'Environment', value: health?.environment ?? 'Unknown', icon: Globe2, ok: !!health },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-7">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">Workspace configuration</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">System settings</h1>
        <p className="mt-2 text-sm text-slate-500">Monitor your BharatVoice services and AI integration mode.</p>
      </header>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-3 border-b border-slate-100 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-50 p-3 text-blue-700"><Activity className="h-5 w-5" /></div>
            <div><h2 className="font-semibold text-slate-900">System health</h2><p className="text-xs text-slate-500">Live status from the FastAPI health endpoint</p></div>
          </div>
          <button onClick={() => void refresh()} disabled={loading} className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh status
          </button>
        </div>
        {loading ? <div className="space-y-4 p-6">{[1,2,3,4].map((n) => <div key={n} className="h-14 animate-pulse rounded-xl bg-slate-100" />)}</div> :
          error ? <div role="alert" className="m-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div> :
          <div className="grid gap-3 p-6 sm:grid-cols-2">
            {rows.map(({ label, value, icon: Icon, ok }) => (
              <div key={label} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 p-4">
                <div className="flex items-center gap-3"><div className="rounded-lg bg-slate-100 p-2 text-slate-600"><Icon className="h-4 w-4" /></div><div><p className="text-xs text-slate-500">{label}</p><p className="mt-0.5 text-sm font-semibold capitalize text-slate-900">{value.replaceAll('_', ' ')}</p></div></div>
                {ok ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <XCircle className="h-5 w-5 text-red-500" />}
              </div>
            ))}
          </div>}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3"><div className="rounded-xl bg-emerald-50 p-3 text-emerald-700"><ShieldCheck className="h-5 w-5" /></div><div><h2 className="font-semibold text-slate-900">AI provider configuration</h2><p className="text-xs text-slate-500">Credentials remain on the backend and are never sent to the browser.</p></div></div>
        <div className="mt-5 rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-600">
          {health?.use_mock_gnani
            ? 'Mock mode is active. Speech requests use deterministic development responses; mock TTS audio is silent and is not real Hindi speech.'
            : 'Live provider mode is configured. Actual STT and TTS requests are routed through the backend to Gnani AI.'}
        </div>
        <p className="mt-4 text-xs text-slate-400">API base URL: {import.meta.env.VITE_API_BASE_URL || '/api'}</p>
      </section>

      <div className="flex items-start gap-3 rounded-xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
        <Clock3 className="mt-0.5 h-5 w-5 shrink-0" /><p>For security, change API keys and provider settings through the backend environment file. Never place secrets in frontend environment variables.</p>
      </div>
    </div>
  );
};

export default Settings;
