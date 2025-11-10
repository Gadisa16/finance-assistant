import { useEffect, useState } from 'react';
import { fetchKpiSummary } from '../services/api';

export default function KpiSummary() {
  const [data, setData] = useState<KpiSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchKpiSummary()
      .then((res: KpiSummary) => { if (!cancelled) setData(res) })
      .catch((err: unknown) => { if (!cancelled) setError((err as Error)?.message || 'Failed to load KPI summary') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="p-3 border border-gray-200 rounded-lg bg-white mt-3">Loading KPI summary…</div>
  if (error) return <div className="p-3 border border-red-300 text-red-700 rounded-lg bg-white mt-3">Error: {String(error)}</div>
  if (!data) return <div className="p-3 border border-gray-200 rounded-lg bg-white mt-3">No data</div>

  const { gross, net, vat, card, cash } = data
  const cardShare = data.card_share ?? (gross ? (card / gross) : 0)

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mt-3">
      <MetricCard label="Gross" value={gross} />
      <MetricCard label="Net" value={net} />
      <MetricCard label="VAT" value={vat} />
      <MetricCard label="Card" value={card} />
      <MetricCard label="Cash" value={cash} />
      <MetricCard label="Card Share" value={cardShare} format={(v)=> (v*100).toFixed(1)+'%'} />
    </div>
  )
}

function MetricCard({ label, value, format }: Readonly<{ label: string; value: number; format?: (v:number)=>string }>) {
  const display = format ? format(value) : value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return (
    <div className="border border-gray-200 rounded-lg p-3 bg-white shadow-sm">
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-xl font-semibold text-gray-900">{display}</div>
    </div>
  )
}
