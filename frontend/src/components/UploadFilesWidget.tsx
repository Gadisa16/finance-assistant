import { useState } from 'react'
import { uploadFiles } from '../services/api'

interface Props {
  month: string
  onSuccess?: (month: string) => void
}

export default function UploadFilesWidget({ month, onSuccess }: Props) {
  const [open, setOpen] = useState(false)
  const [salesFile, setSalesFile] = useState<File | null>(null)
  const [bankFile, setBankFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<number | null>(null)
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  async function handleUpload() {
    if (!salesFile || !bankFile) {
      setMsg({ type: 'error', text: 'Please choose both files.' })
      return
    }
    setLoading(true)
    setMsg(null)
    try {
      // Wrap uploadFiles to capture progress by temporarily adding interceptor
      const res = await uploadFiles(month, salesFile, bankFile)
      setMsg({ type: 'success', text: `Uploaded: sales ${res.sales_rows}, bank ${res.bank_rows}` })
      onSuccess?.(res.month)
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      if (detail?.error === 'month_mismatch') {
        setMsg({ type: 'error', text: `Month mismatch: requested ${detail.requested_month}. Excel months: ${detail.excel_months_found?.join(',') || 'none'} Bank months: ${detail.bank_months_found?.join(',') || 'none'}` })
      } else if (e?.code === 'ECONNABORTED') {
        setMsg({ type: 'error', text: 'Upload timeout. Large files may need a retry; please try again.' })
      } else {
        setMsg({ type: 'error', text: e?.message || 'Upload failed' })
      }
    } finally {
      setLoading(false)
      setProgress(null)
      setTimeout(() => setMsg(null), 7000)
    }
  }

  return (
    <div className="absolute top-4 right-4 text-xs z-40">
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-3 py-2 shadow flex items-center gap-1"
          aria-label="Open upload panel"
        >
          ⬆ Upload Documents
        </button>
      )}
      {open && (
        <div className="w-72 bg-white border border-gray-300 rounded-md shadow-md p-3 space-y-2">
          <div className="flex items-center justify-between mb-1">
            <h2 className="font-semibold text-gray-700 text-sm">Upload Data (Month {month})</h2>
            <button
              onClick={() => setOpen(false)}
              className="text-gray-500 hover:text-gray-700"
              aria-label="Close upload panel"
            >✕</button>
          </div>
          <div className="flex flex-col gap-2">
            <label className="flex flex-col gap-1">
              <span className="text-gray-600">Sales Excel</span>
              <input
                type="file"
                accept=".xls,.xlsx"
                onChange={e => setSalesFile(e.target.files?.[0] || null)}
                className="text-[11px]"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-gray-600">Bank PDF</span>
              <input
                type="file"
                accept=".pdf"
                onChange={e => setBankFile(e.target.files?.[0] || null)}
                className="text-[11px]"
              />
            </label>
            <button
              onClick={handleUpload}
              disabled={loading || !salesFile || !bankFile}
              className="mt-1 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white py-1 rounded text-xs"
            >
              {loading ? 'Uploading…' : 'Upload'}
            </button>
            {progress != null && (
              <div className="h-2 bg-gray-200 rounded">
                <div
                  className="h-2 bg-indigo-600 rounded"
                  style={{ width: `${progress}%`, transition: 'width .3s' }}
                />
              </div>
            )}
            {msg && (
              <div className={`rounded px-2 py-1 ${msg.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                {msg.text}
              </div>
            )}
            <p className="text-[10px] text-gray-500 leading-snug">
              Large files may take several seconds. If timeout occurs, try again; parsing is CPU intensive.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
