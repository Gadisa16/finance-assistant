import axios, { AxiosError, AxiosResponse } from 'axios'

// Resolve API base URL robustly for both Docker and local dev
const envUrl: string | undefined = (import.meta as any)?.env?.VITE_API_URL
let baseURL = envUrl
if (!baseURL && typeof globalThis !== 'undefined') {
  const host = (globalThis as any)?.location?.hostname
  // If opened from host browser (localhost), default to backend on localhost
  // Otherwise (rare), keep Docker service fallback
  baseURL = (host === 'localhost' || host === '127.0.0.1')
    ? 'http://localhost:8000'
    : 'http://backend:8000'
}

export const api = axios.create({
  baseURL,
  timeout: 60000,
})

api.interceptors.response.use(
  (r: AxiosResponse) => r,
  (err: AxiosError) => Promise.reject(err)
)

export async function get<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const res = await api.get<T>(path, { params })
  return res.data
}

// Normalize helpers
function normalizeKpiSummary(raw: any): KpiSummary {
  const gross = raw?.gross ?? raw?.total_gross ?? 0
  const net = raw?.net ?? raw?.total_net ?? 0
  const vat = raw?.vat ?? raw?.total_vat ?? 0
  const card = raw?.card ?? raw?.card_gross ?? 0
  const cash = raw?.cash ?? raw?.cash_gross ?? 0
  const card_share = raw?.card_share ?? (gross ? card / gross : undefined)
  return { gross, net, vat, card, cash, card_share }
}

function normalizeDailyKpi(arr: any[]): DailyKpiItem[] {
  return (Array.isArray(arr) ? arr : []).map((d) => ({
    date: d?.date ?? d?.day ?? d?.ds ?? '',
    gross: d?.gross ?? d?.total_gross ?? 0,
    card: d?.card ?? d?.card_gross ?? 0,
    cash: d?.cash ?? d?.cash_gross ?? 0,
  })).filter((d) => d.date)
}

function normalizeVatReport(arr: any[]): VatReport {
  return (Array.isArray(arr) ? arr : []).map((r) => ({
    rate: Number(r?.rate ?? r?.vat_rate ?? 0),
    net: Number(r?.net ?? r?.total_net ?? 0),
    vat: Number(r?.vat ?? r?.total_vat ?? 0),
    gross: Number(r?.gross ?? r?.total_gross ?? 0),
  }))
}

function normalizeReconciliation(arr: any[]): ReconciliationRow[] {
  return (Array.isArray(arr) ? arr : []).map((r) => ({
    date: String(r?.date ?? r?.day ?? r?.ds ?? ''),
    sales_card: Number(r?.sales_card ?? r?.card ?? r?.card_gross ?? 0),
    bank_tpa: Number(r?.bank_tpa ?? r?.tpa ?? 0),
    fees: (r?.fees === null || r?.fees === undefined) ? undefined : Number(r?.fees),
    delta: Number(r?.delta ?? 0),
    detail: r?.detail ?? r?.detail_json,
  })).filter((r) => r.date)
}

// Endpoint helpers (typed)
export const fetchKpiSummary = async (month: string): Promise<KpiSummary> => {
  const raw = await get<any>('/kpi/summary', { month })
  return normalizeKpiSummary(raw)
}

export const fetchKpiDaily = async (month: string): Promise<DailyKpiItem[]> => {
  const raw = await get<any[]>('/kpi/daily', { month })
  return normalizeDailyKpi(raw)
}

export const fetchVatReport = async (month: string): Promise<VatReport> => {
  const raw = await get<any[]>('/vat/report', { month })
  return normalizeVatReport(raw)
}

export const fetchReconciliation = async (month: string): Promise<ReconciliationRow[]> => {
  const raw = await get<any[]>('/recon/card', { month })
  return normalizeReconciliation(raw)
}

// Top lists
export interface TopProduct { product: string; gross: number }
export interface TopCustomer { customer: string; gross: number }

export const fetchTopProducts = async (month: string, limit: number = 10): Promise<TopProduct[]> => {
  const raw = await get<any[]>('/kpi/top-products', { month, limit })
  return (Array.isArray(raw) ? raw : []).map(r => ({
    product: String(r?.product ?? ''),
    gross: Number(r?.gross ?? 0)
  })).filter(r => r.product)
}

export const fetchTopCustomers = async (month: string, limit: number = 10): Promise<TopCustomer[]> => {
  const raw = await get<any[]>('/kpi/top-customers', { month, limit })
  return (Array.isArray(raw) ? raw : []).map(r => ({
    customer: String(r?.customer ?? ''),
    gross: Number(r?.gross ?? 0)
  })).filter(r => r.customer)
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export const askChat = async (month: string, question: string): Promise<string> => {
  const res = await api.post<{ answer: string }>('/chat/ask', { month, question })
  return res.data.answer
}

export interface UploadResult {
  sales_rows: number
  bank_rows: number
  month: string
}

export const uploadFiles = async (
  month: string,
  salesFile: File,
  bankFile: File
): Promise<UploadResult> => {
  const form = new FormData()
  form.append('sales_excel', salesFile)
  form.append('bank_pdf', bankFile)
  const res = await api.post<UploadResult>(`/files/upload`, form, {
    params: { month },
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000, // allow heavy Excel/PDF parsing
    onUploadProgress: (evt) => {
      // optional hook: consumers can attach a listener by patching api.interceptors if needed
    }
  })
  return res.data
}

export default api