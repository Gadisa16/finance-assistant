import { useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { fetchKpiDaily } from '../services/api';
import './daily-chart.css';

interface DailyEntryRaw {
  date?: string; day?: string; ds?: string;
  gross?: number; total_gross?: number;
  card?: number; card_gross?: number;
  cash?: number; cash_gross?: number;
}

interface DailyEntryNorm {
  date: string;
  gross: number;
  card: number;
  cash: number;
}

export default function DailyChart({ month }: { month: string }) {
  const [data, setData] = useState<DailyEntryRaw[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<'bar' | 'line'>('bar')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchKpiDaily(month)
      .then((res: DailyKpiItem[]) => {
        if (cancelled) return
        // Each item already normalized; map into raw shape for reuse of existing mapping logic.
        const raw: DailyEntryRaw[] = res.map(r => ({ date: r.date, gross: r.gross, card: r.card, cash: r.cash }))
        setData(raw)
      })
      .catch((err: unknown) => { if (!cancelled) setError((err as Error)?.message || 'Failed to load daily KPI') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [month])

  const chartData: DailyEntryNorm[] = useMemo(() => {
    return (data || []).map((d: DailyEntryRaw) => ({
      date: d.date || d.day || d.ds || '',
      gross: d.gross ?? d.total_gross ?? 0,
      card: d.card ?? d.card_gross ?? 0,
      cash: d.cash ?? d.cash_gross ?? 0,
    })).filter((d: DailyEntryNorm) => d.date)
  }, [data])

  if (loading) return <div className="p-3 border border-gray-200 rounded-lg bg-white mt-3">Loading daily KPI…</div>
  if (error) return <div className="p-3 border border-red-300 text-red-700 rounded-lg bg-white mt-3">Error: {String(error)}</div>
  if (!chartData.length) return <div className="p-3 border border-gray-200 rounded-lg bg-white mt-3">No data</div>

  return (
    <div className="border border-gray-200 rounded-lg bg-white p-3 mt-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-medium">Daily KPI</h3>
        <div className="space-x-2">
          <button onClick={() => setMode('bar')} className={btnClass(mode==='bar')}>Bar</button>
          <button onClick={() => setMode('line')} className={btnClass(mode==='line')}>Line</button>
        </div>
      </div>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          {mode === 'bar' ? (
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="gross" name="Gross" fill="#6366F1" />
              <Bar dataKey="card" name="Card" fill="#10B981" />
              <Bar dataKey="cash" name="Cash" fill="#F59E0B" />
            </BarChart>
          ) : (
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="gross" name="Gross" stroke="#6366F1" strokeWidth={2} />
              <Line type="monotone" dataKey="card" name="Card" stroke="#10B981" strokeWidth={2} />
              <Line type="monotone" dataKey="cash" name="Cash" stroke="#F59E0B" strokeWidth={2} />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function btnClass(active: boolean) {
  return [
    'px-3 py-1 rounded-md border text-sm',
    active ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'
  ].join(' ')
}
