import { useEffect, useMemo, useState } from 'react'
import { fetchReconciliation } from '../services/api'

interface Props {
  month: string
}

export default function ReconciliationTable({ month }: Readonly<Props>) {
  const [rows, setRows] = useState<ReconciliationRow[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchReconciliation(month)
      .then((data: ReconciliationRow[]) => { if (!cancelled) setRows(data) })
      .catch((err: unknown) => { if (!cancelled) setError((err as Error)?.message || 'Failed to load reconciliation') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [month])

  const totals = useMemo(() => {
    const base = { sales_card: 0, bank_tpa: 0, fees: 0, delta: 0 }
    if (!rows) return base
    return rows.reduce((acc, r) => {
      acc.sales_card += r.sales_card || 0
      acc.bank_tpa += r.bank_tpa || 0
      acc.fees += r.fees || 0
      acc.delta += r.delta || 0
      return acc
    }, base)
  }, [rows])

  if (loading) return <div className="p-3 border border-gray-200 rounded-lg bg-white mt-3">Loading reconciliation…</div>
  if (error) return <div className="p-3 border border-red-300 text-red-700 rounded-lg bg-white mt-3">Error: {error}</div>
  if (!rows || rows.length === 0) return <div className="p-3 border border-gray-200 rounded-lg bg-white mt-3">No reconciliation data</div>

  return (
    <div className="border border-gray-200 rounded-lg bg-white p-3 mt-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-medium">Card vs Bank TPA Reconciliation</h3>
        <span className={`text-xs px-2 py-1 rounded-full ${Math.abs(totals.delta) < 0.005 ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
          {Math.abs(totals.delta) < 0.005 ? 'Balanced' : 'Check deltas'}
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr className="text-left">
              <th className="px-3 py-2 font-semibold text-gray-600">Date</th>
              <th className="px-3 py-2 font-semibold text-gray-600">Sales (Card)</th>
              <th className="px-3 py-2 font-semibold text-gray-600">Bank TPA</th>
              <th className="px-3 py-2 font-semibold text-gray-600">Fees</th>
              <th className="px-3 py-2 font-semibold text-gray-600">Delta</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.date} className="odd:bg-white even:bg-gray-50 border-b last:border-b-0">
                <td className="px-3 py-2 whitespace-nowrap">{r.date}</td>
                <td className="px-3 py-2">{format(r.sales_card)}</td>
                <td className="px-3 py-2">{format(r.bank_tpa)}</td>
                <td className="px-3 py-2">{r.fees != null ? format(r.fees) : '-'}</td>
                <td className={`px-3 py-2 font-medium ${Math.abs(r.delta) < 0.005 ? 'text-green-600' : 'text-amber-700'}`}>{format(r.delta)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-gray-100 font-semibold">
              <td className="px-3 py-2">Total</td>
              <td className="px-3 py-2">{format(totals.sales_card)}</td>
              <td className="px-3 py-2">{format(totals.bank_tpa)}</td>
              <td className="px-3 py-2">{format(totals.fees)}</td>
              <td className={`px-3 py-2 ${Math.abs(totals.delta) < 0.005 ? 'text-green-700' : 'text-amber-700'}`}>{format(totals.delta)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}

function format(n: number) {
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
