import { useEffect, useState } from 'react'
import { fetchTopCustomers, fetchTopProducts, TopCustomer, TopProduct } from '../services/api'

interface Props {
  month: string
  limit?: number
}

export default function TopLists({ month, limit = 10 }: Props) {
  const [products, setProducts] = useState<TopProduct[]>([])
  const [customers, setCustomers] = useState<TopCustomer[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    Promise.all([
      fetchTopProducts(month, limit),
      fetchTopCustomers(month, limit)
    ])
      .then(([p, c]) => {
        if (cancelled) return
        setProducts(p)
        setCustomers(c)
      })
      .catch((e) => {
        if (cancelled) return
        setError(e?.message || 'Failed to load top lists')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [month, limit])

  return (
    <div className="mt-4">
      <h2 className="text-xl font-semibold mb-2">Top Customers & Products</h2>
      {loading && <div className="text-sm text-gray-600">Loading...</div>}
      {error && <div className="text-sm text-red-600">{error}</div>}
      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border rounded-md p-3 bg-white">
            <h3 className="font-medium mb-2">Top Products</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-1">#</th>
                  <th className="py-1">Product</th>
                  <th className="py-1 text-right">Gross</th>
                </tr>
              </thead>
              <tbody>
                {products.length === 0 && (
                  <tr><td colSpan={3} className="py-2 text-gray-500">No data</td></tr>
                )}
                {products.map((p, idx) => (
                  <tr key={p.product + idx} className="border-t">
                    <td className="py-1 w-8">{idx + 1}</td>
                    <td className="py-1 truncate" title={p.product}>{p.product}</td>
                    <td className="py-1 text-right">{p.gross.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="border rounded-md p-3 bg-white">
            <h3 className="font-medium mb-2">Top Customers</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-1">#</th>
                  <th className="py-1">Customer</th>
                  <th className="py-1 text-right">Gross</th>
                </tr>
              </thead>
              <tbody>
                {customers.length === 0 && (
                  <tr><td colSpan={3} className="py-2 text-gray-500">No data</td></tr>
                )}
                {customers.map((c, idx) => (
                  <tr key={c.customer + idx} className="border-t">
                    <td className="py-1 w-8">{idx + 1}</td>
                    <td className="py-1 truncate" title={c.customer}>{c.customer}</td>
                    <td className="py-1 text-right">{c.gross.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
