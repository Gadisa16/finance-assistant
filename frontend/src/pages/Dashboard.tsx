import { useState } from 'react'
import DailyChart from '../components/DailyChart'
import KpiSummary from '../components/KpiSummary'
import ReconciliationTable from '../components/ReconciliationTable'
import VatReport from '../components/VatReport'

export default function Dashboard() {
  const [month, setMonth] = useState<string>('09')

  return (
    <div className="p-4 font-sans">
      <h1 className="text-2xl font-semibold mb-3">Finance Assistant</h1>
      <label className="inline-flex items-center gap-2 text-sm mb-2">
        <span>Month:</span>
        <select
          value={month}
          onChange={e => setMonth(e.target.value)}
          className="border border-gray-300 rounded-md px-2 py-1 bg-white"
        >
          {Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0')).map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </label>

  <KpiSummary month={month} />
  <DailyChart month={month} />
  <VatReport month={month} />
      <ReconciliationTable month={month} />
    </div>
  )
}
