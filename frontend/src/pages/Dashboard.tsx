import { useState } from 'react'
import ChatWidget from '../components/ChatWidget'
import DailyChart from '../components/DailyChart'
import KpiSummary from '../components/KpiSummary'
import ReconciliationTable from '../components/ReconciliationTable'
import TopLists from '../components/TopLists'
import UploadFilesWidget from '../components/UploadFilesWidget'
import VatReport from '../components/VatReport'

export default function Dashboard() {
  const [month, setMonth] = useState<string>('09')
  const [refresh, setRefresh] = useState<number>(0)

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

  <KpiSummary key={`kpi-${month}-${refresh}`} month={month} />
  <DailyChart key={`daily-${month}-${refresh}`} month={month} />
  <VatReport key={`vat-${month}-${refresh}`} month={month} />
  <TopLists key={`top-${month}-${refresh}`} month={month} />
      <ReconciliationTable key={`recon-${month}-${refresh}`} month={month} />
      <ChatWidget month={month} />
      <UploadFilesWidget month={month} onSuccess={() => {
        // Increment refresh counter to force remount + refetch of data components
        setRefresh(r => r + 1)
      }} />
    </div>
  )
}
