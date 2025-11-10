import { useEffect, useState } from 'react'
import { fetchVatReport } from '../services/api'

export default function VatReport({ month }: Readonly<{ month: string }>) {
  const [rows, setRows] = useState<VatReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchVatReport(month)
      .then((data: VatReport) => { if (!cancelled) setRows(data) })
      .catch((err: unknown) => { if (!cancelled) setError((err as Error)?.message || 'Failed to load VAT report') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [month])

  if (loading) return <div className="p-3 border border-gray-200 rounded-lg bg-white mt-3">Loading VAT report…</div>
  if (error) return <div className="p-3 border border-red-300 text-red-700 rounded-lg bg-white mt-3">Error: {error}</div>
  if (!rows || rows.length === 0) return <div className="p-3 border border-gray-200 rounded-lg bg-white mt-3">No VAT data</div>

  // Totals
  const total = rows.reduce((acc, r) => {
    acc.net += r.net; acc.vat += r.vat; acc.gross += r.gross; return acc
  }, { net: 0, vat: 0, gross: 0 })

  return (
    <div className="border border-gray-200 rounded-lg bg-white p-3 mt-3">
      <h3 className="text-lg font-medium mb-2">VAT Breakdown</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr className="text-left">
              <th className="px-3 py-2 font-semibold text-gray-600">Rate %</th>
              <th className="px-3 py-2 font-semibold text-gray-600">Net</th>
              <th className="px-3 py-2 font-semibold text-gray-600">VAT</th>
              <th className="px-3 py-2 font-semibold text-gray-600">Gross</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.rate} className="odd:bg-white even:bg-gray-50 border-b last:border-b-0">
                <td className="px-3 py-2">{r.rate}</td>
                <td className="px-3 py-2">{format(r.net)}</td>
                <td className="px-3 py-2">{format(r.vat)}</td>
                <td className="px-3 py-2">{format(r.gross)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-gray-100 font-semibold">
              <td className="px-3 py-2">Total</td>
              <td className="px-3 py-2">{format(total.net)}</td>
              <td className="px-3 py-2">{format(total.vat)}</td>
              <td className="px-3 py-2">{format(total.gross)}</td>
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
