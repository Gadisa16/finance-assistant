import axios, { AxiosError, AxiosResponse } from 'axios'

const baseURL = (import.meta as any)?.env?.VITE_API_URL || 'http://backend:8000'

export const api = axios.create({
  baseURL,
  timeout: 10000,
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
    fees: r?.fees != null ? Number(r?.fees) : undefined,
    delta: Number(r?.delta ?? 0),
    detail: r?.detail ?? r?.detail_json,
  })).filter((r) => r.date)
}

// Endpoint helpers (typed)
export const fetchKpiSummary = async (): Promise<KpiSummary> => {
  const raw = await get<any>('/kpi/summary')
  return normalizeKpiSummary(raw)
}

export const fetchKpiDaily = async (month: string): Promise<DailyKpiItem[]> => {
  const raw = await get<any[]>('/kpi/daily', { month })
  return normalizeDailyKpi(raw)
}

export const fetchVatReport = async (): Promise<VatReport> => {
  const raw = await get<any[]>('/vat/report')
  return normalizeVatReport(raw)
}

export const fetchReconciliation = async (month: string): Promise<ReconciliationRow[]> => {
  const raw = await get<any[]>('/recon/card', { month })
  return normalizeReconciliation(raw)
}

export default api