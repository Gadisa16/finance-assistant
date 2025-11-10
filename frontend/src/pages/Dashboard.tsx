import { useState } from 'react'
import ChatWidget from '../components/ChatWidget'
import DailyChart from '../components/DailyChart'
import KpiSummary from '../components/KpiSummary'
import ReconciliationTable from '../components/ReconciliationTable'
import UploadFilesWidget from '../components/UploadFilesWidget'
import VatReport from '../components/VatReport'

export default function Dashboard() {
  const [month, setMonth] = useState<string>('09')

  return (
    <div className="p-4 font-sans relative min-h-screen">
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
      <ChatWidget month={month} />
      <UploadFilesWidget month={month} onSuccess={() => {
        // Trigger a lightweight refetch by toggling month state to same value (forces child effects if implemented)
        setMonth(m => m)
      }} />
    </div>
  )
}
