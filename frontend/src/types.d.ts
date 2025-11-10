declare module '*.css';
declare module '*.scss';
declare module '*.png';
declare module '*.jpg';
declare module '*.jpeg';
declare module '*.gif';
declare module '*.svg' {
  import type React from 'react'
  const content: React.FunctionComponent<React.SVGAttributes<SVGElement>>
  export default content
}

// Fallback shim if type packages are missing
declare module 'recharts'

// -----------------------------
// App domain types
// -----------------------------

// KPI Summary (normalized)
interface KpiSummary {
  gross: number
  net: number
  vat: number
  card: number
  cash: number
  card_share?: number
}

// Daily KPI (normalized)
interface DailyKpiItem {
  date: string
  gross: number
  card: number
  cash: number
}

// VAT report rows
interface VatReportRow {
  rate: number
  net: number
  vat: number
  gross: number
}
type VatReport = VatReportRow[]

// Reconciliation rows (per day)
interface ReconciliationRow {
  date: string
  sales_card: number
  bank_tpa: number
  fees?: number
  delta: number
  detail?: unknown
}

// Generic async state shape for hooks/components
interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
}
