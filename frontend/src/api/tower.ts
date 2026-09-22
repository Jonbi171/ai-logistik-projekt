export type Page =
  | 'Control Tower'
  | 'Transportation'
  | 'Inventory'
  | 'Demand'
  | 'Suppliers'
  | 'Production'
  | 'AI / ML Insights'
  | 'Scenario Analysis'
export type Risk = 'High' | 'Medium' | 'Low' | 'Not scored'
export interface KPI {
  label: string
  value: number | null
  unit: string
  detail: string
  definition: string
  tone: string
}
export interface Overview {
  source: { source: string; extracted_at: string; offline: boolean }
  as_of: string
  history_from: string
  history_to: string
  kpis: KPI[]
  trend: { month: string; on_time: number; shipments: number; freight: number }[]
  counts: {
    shipments: number
    replay_shipments: number
    high_delay: number
    shortages: number
    anomalies: number
    suppliers: number
    exceptions: number
    inventory_value: number
  }
  quality: { check: string; value: number; note: string }[]
  limitations: string[]
  locations: {
    id: string
    name: string
    city: string
    location_type: string
    latitude: number
    longitude: number
  }[]
  lanes: { origin_location_id: string; destination_location_id: string; shipments: number }[]
  risk_distribution: { name: string; count: number }[]
}
export interface Shipment {
  id: string
  shipment_number: string
  origin: string
  destination: string
  carrier: string
  carrier_id: string
  transport_mode: string
  service_level: string
  status: string
  planned_departure_at: string
  planned_arrival_at: string
  actual_arrival_at: string
  current_eta: string
  predicted_eta: string
  late_probability: number
  predicted_delay: number
  predicted_cost: number
  freight_cost_sek: number
  target_delay: number
  distance_km: number
  total_weight_kg: number
  total_volume_m3: number
  risk: Risk
  anomaly: boolean
  anomaly_score: number
  cost_ratio: number | null
  orders: string
  priority: string
  context: string[]
}
export interface Inventory {
  id: string
  product_id: string
  location_id: string
  sku: string
  product: string
  location: string
  available: number
  on_hand: number
  safety_stock: number
  reorder_point: number
  inventory_value: number
  unit_cost: number
  forecast_demand: number | null
  daily_demand: number | null
  incoming: number
  excess: boolean
  as_of: string
  forecast_origin: string | null
  method: string
  action: string
  risk: Risk
  days_of_supply: number | null
  projected_balance: number | null
  shortage: number | null
  shortage_day: number | null
  transfer: { from: string; quantity: number; days_before: number; days_after: number } | null
}
export interface Forecast {
  product_id: string
  sku: string
  product: string
  model: string
  weeks: number
  next_4_weeks: number
  weekly: number
  sigma: number
  methodology: string
  metrics: Record<string, number | null>
  baseline: Record<string, number | null>
  history: { week: string; actual: number; backtest: number | null }[]
  future: { week: string; forecast: number; lower: number; upper: number }[]
}
export interface Supplier {
  id: string
  name: string
  country: string
  orders: number
  on_time: number
  lead_days: number
  fill_rate: number
  rejection_rate: number
  late_probability: number | null
  risk: Risk
  action: string
}
export interface Production {
  plan_attainment: number
  scrap_rate: number
  utilization: number
  late_rate: number
  downtime_hours: number
  definition: string
  monthly: {
    month: string
    planned: number
    actual: number
    utilization: number
    downtime: number
  }[]
  orders: {
    production_order_number: string
    plant: string
    product: string
    planned_quantity: number
    produced_quantity: number
    scrapped_quantity: number
    status: string
  }[]
}
export interface ModelCard {
  id: string
  name: string
  model: string
  purpose: string
  target: string
  features: string[]
  observations: number
  train_rows: number
  test_rows: number
  cutoff?: string
  trained_at: string
  metrics: Record<string, number | number[][] | null>
  comparison: { model: string; metrics: Record<string, number | number[][] | null> } | null
  importance: { feature: string; importance: number }[]
  reason: string
  validation: string
  samples?: { actual: number; predicted: number }[]
}
export interface Exception {
  id: string
  type: string
  severity: Risk
  object: string
  trigger: string
  kpi: string
  impact: string
  action: string
  expected_impact: string
  page: Page
  reference: string
  replay: boolean
  score: number
}
export interface ShipmentList {
  items: Shipment[]
  total: number
  offset: number
  replay: boolean
}
export interface TransportResult {
  baseline: { cost: number; cost_per_km: number; late_probability: number; delay_hours: number }
  scenario: {
    cost: number
    cost_per_km: number
    late_probability: number
    delay_hours: number
    historical_average: number | null
    comparable_count: number
  }
  warnings: string[]
  assumptions: string
}
export interface Projection {
  projected_balance: number
  shortage: number
  shortage_day: number | null
  risk: Risk
  days_of_supply: number
  trajectory: { day: number; balance: number }[]
}
export interface InventoryResult {
  baseline: Projection
  scenario: Projection
  incremental_inventory_value: number
  assumptions: string
}
export async function api<T>(path: string, signal?: AbortSignal, body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {
    signal,
    method: body ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json' },
    ...(body ? { body: JSON.stringify(body) } : {}),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(
      typeof error.detail === 'string'
        ? error.detail
        : `Request failed (${response.status}). Check the backend connection.`,
    )
  }
  return response.json() as Promise<T>
}
