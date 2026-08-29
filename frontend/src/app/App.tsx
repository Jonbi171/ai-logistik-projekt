import { useEffect, useMemo, useState } from 'react'
import { fetchDashboard } from '../api/dashboard'
import { API_ENDPOINTS, type ApiEndpoint } from '../api/endpoints'
import type { ApiValue, DashboardResponse } from '../api/types'
import './App.css'

type DashboardId =
  | 'inventory'
  | 'shipments'
  | 'sales'
  | 'purchasing'
  | 'movements'
  | 'bom'
  | 'suppliers'
  | 'tracking'

type Column = {
  label: string
  path: string
  tone?: boolean
}

type DashboardConfig = {
  eyebrow: string
  title: string
  description: string
  endpoint: ApiEndpoint
  columns: Column[]
}

const dashboards: Record<DashboardId, DashboardConfig> = {
  inventory: {
    eyebrow: 'Inventory',
    title: 'Inventory overview',
    description: 'Live stock position and availability across every location.',
    endpoint: API_ENDPOINTS.currentInventory,
    columns: [
      { label: 'SKU', path: 'product.sku' },
      { label: 'Product', path: 'product.name' },
      { label: 'Location', path: 'location.name' },
      { label: 'Available', path: 'quantities.available' },
      { label: 'On hand', path: 'quantities.on_hand' },
      { label: 'Status', path: 'status', tone: true },
    ],
  },
  shipments: {
    eyebrow: 'Logistics',
    title: 'Shipment performance',
    description: 'Follow active shipments, delays, carriers and current ETAs.',
    endpoint: API_ENDPOINTS.shipmentOverview,
    columns: [
      { label: 'Shipment', path: 'shipment_number' },
      { label: 'Origin', path: 'route.origin.name' },
      { label: 'Destination', path: 'route.destination.name' },
      { label: 'Carrier', path: 'transport.carrier' },
      { label: 'ETA', path: 'schedule.current_eta' },
      { label: 'Status', path: 'status', tone: true },
    ],
  },
  sales: {
    eyebrow: 'Orders',
    title: 'Sales order fulfillment',
    description: 'Monitor customer orders, remaining quantities and fulfillment.',
    endpoint: API_ENDPOINTS.salesOrderOverview,
    columns: [
      { label: 'Order', path: 'order.number' },
      { label: 'Customer', path: 'order.customer' },
      { label: 'Product', path: 'line.product_name' },
      { label: 'Ordered', path: 'line.ordered' },
      { label: 'Remaining', path: 'line.remaining' },
      { label: 'Status', path: 'order.status', tone: true },
    ],
  },
  purchasing: {
    eyebrow: 'Orders',
    title: 'Purchase order performance',
    description: 'Review inbound orders, supplier lead times and on-time delivery.',
    endpoint: API_ENDPOINTS.purchaseOrderOverview,
    columns: [
      { label: 'Purchase order', path: 'purchase_order.number' },
      { label: 'Supplier', path: 'supplier.name' },
      { label: 'Product', path: 'line.product_name' },
      { label: 'Outstanding', path: 'line.outstanding' },
      { label: 'Destination', path: 'destination' },
      { label: 'Status', path: 'purchase_order.status', tone: true },
    ],
  },
  movements: {
    eyebrow: 'Inventory',
    title: 'Inventory movement history',
    description: 'Trace stock changes, reasons and linked logistics documents.',
    endpoint: API_ENDPOINTS.inventoryHistory,
    columns: [
      { label: 'Time', path: 'event_timestamp' },
      { label: 'Product', path: 'product.name' },
      { label: 'Location', path: 'location.name' },
      { label: 'Movement', path: 'movement.type', tone: true },
      { label: 'Quantity', path: 'movement.quantity' },
      { label: 'Reason', path: 'movement.reason' },
    ],
  },
  bom: {
    eyebrow: 'Planning',
    title: 'Bill of materials',
    description: 'Explore component relationships and material requirements.',
    endpoint: API_ENDPOINTS.productBom,
    columns: [
      { label: 'Finished product', path: 'finished_product.name' },
      { label: 'Component', path: 'component.name' },
      { label: 'Quantity', path: 'material_requirement.quantity' },
      { label: 'With scrap', path: 'material_requirement.quantity_including_scrap' },
      { label: 'Unit', path: 'component.unit_of_measure' },
      { label: 'Version', path: 'bom_version' },
    ],
  },
  suppliers: {
    eyebrow: 'Suppliers',
    title: 'Product suppliers',
    description: 'Compare sourcing terms, supplier risk and contracted capacity.',
    endpoint: API_ENDPOINTS.productSupplierOverview,
    columns: [
      { label: 'Product', path: 'product.name' },
      { label: 'Supplier', path: 'supplier.name' },
      { label: 'Risk', path: 'supplier.risk_tier', tone: true },
      { label: 'Unit cost', path: 'commercial_terms.unit_cost_sek' },
      { label: 'Lead time', path: 'commercial_terms.lead_time_days' },
      { label: 'Preferred', path: 'supplier.preferred', tone: true },
    ],
  },
  tracking: {
    eyebrow: 'Logistics',
    title: 'Shipment event tracking',
    description: 'See the latest milestones reported throughout each journey.',
    endpoint: API_ENDPOINTS.shipmentEvents,
    columns: [
      { label: 'Shipment', path: 'shipment_number' },
      { label: 'Event', path: 'event.type' },
      { label: 'Status', path: 'event.status_code', tone: true },
      { label: 'Location', path: 'location.name' },
      { label: 'City', path: 'location.city' },
      { label: 'Time', path: 'event.timestamp' },
    ],
  },
}

const menuGroups: { label: string; items: DashboardId[] }[] = [
  { label: 'Inventory', items: ['inventory', 'movements'] },
  { label: 'Orders', items: ['sales', 'purchasing'] },
  { label: 'Logistics', items: ['shipments', 'tracking'] },
  { label: 'Supply', items: ['suppliers', 'bom'] },
]

const formatLabel = (key: string) =>
  key
    .replace(/_percent$/, '')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())

const formatDate = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime()) || !value.match(/^\d{4}-\d{2}-\d{2}/)) return value
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    ...(value.includes('T') ? { hour: '2-digit', minute: '2-digit' } : {}),
  }).format(date)
}

const formatValue = (value: unknown, key = ''): string => {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') {
    const formatted = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 2 }).format(value)
    if (key.includes('percent')) return `${formatted}%`
    if (key.includes('sek')) return `${formatted} SEK`
    return formatted
  }
  if (typeof value === 'object') {
    return Object.entries(value)
      .map(([label, amount]) => `${formatLabel(label)} ${String(amount)}`)
      .join(' · ')
  }
  return formatDate(String(value))
}

const getValue = (row: Record<string, unknown>, path: string): unknown =>
  path.split('.').reduce<unknown>((value, key) => {
    if (typeof value !== 'object' || value === null) return undefined
    return (value as Record<string, unknown>)[key]
  }, row)

const metricEntries = (summary: Record<string, ApiValue>) =>
  Object.entries(summary)
    .filter(([key]) => !key.endsWith('_definition') && key !== 'returned_records')
    .slice(0, 4)

function Mark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <span />
      <span />
      <span />
    </span>
  )
}

function App() {
  const [activeId, setActiveId] = useState<DashboardId>('inventory')
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const config = dashboards[activeId]

  useEffect(() => {
    const controller = new AbortController()

    fetchDashboard(config.endpoint, controller.signal)
      .then((response) => {
        setData(response)
        setLastUpdated(new Date())
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setData(null)
        setError(requestError instanceof Error ? requestError.message : 'Unable to load dashboard data')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [config.endpoint, refreshKey])

  const metrics = useMemo(() => (data ? metricEntries(data.summary) : []), [data])

  const chooseDashboard = (id: DashboardId) => {
    if (id !== activeId) {
      setLoading(true)
      setError(null)
    }
    setActiveId(id)
    document.querySelectorAll<HTMLDetailsElement>('.nav-dropdown[open]').forEach((menu) => {
      menu.open = false
    })
  }

  const refreshDashboard = () => {
    setLoading(true)
    setError(null)
    setRefreshKey((key) => key + 1)
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" type="button" onClick={() => chooseDashboard('inventory')}>
          <Mark />
          <span>BillgerICT</span>
        </button>

        <nav className="main-nav" aria-label="KPI dashboards">
          {menuGroups.map((group) => (
            <details className="nav-dropdown" key={group.label}>
              <summary>
                {group.label}
                <span className="chevron" aria-hidden="true">⌄</span>
              </summary>
              <div className="dropdown-menu">
                <span className="dropdown-caption">KPI displays</span>
                {group.items.map((id) => (
                  <button
                    className={activeId === id ? 'active' : ''}
                    key={id}
                    type="button"
                    onClick={() => chooseDashboard(id)}
                  >
                    <span>{dashboards[id].title}</span>
                    <small>{dashboards[id].description}</small>
                  </button>
                ))}
              </div>
            </details>
          ))}
        </nav>

        <div className="header-actions">
          <span className="connection"><i /> Live data</span>
          <button className="avatar" type="button" aria-label="Open profile">JB</button>
        </div>
      </header>

      <main>
        <section className="page-heading">
          <div>
            <span className="eyebrow">{config.eyebrow} intelligence</span>
            <h1>{config.title}</h1>
            <p>{config.description}</p>
          </div>
          <div className="heading-actions">
            {lastUpdated && <span className="updated">Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>}
            <button className="refresh-button" type="button" onClick={refreshDashboard} disabled={loading}>
              <span aria-hidden="true">↻</span> Refresh
            </button>
          </div>
        </section>

        {error ? (
          <section className="error-state" role="alert">
            <span className="error-icon">!</span>
            <div>
              <h2>We could not reach the data service</h2>
              <p>{error}. Confirm that the FastAPI service is running and try again.</p>
            </div>
            <button type="button" onClick={refreshDashboard}>Try again</button>
          </section>
        ) : (
          <>
            <section className="metrics-grid" aria-label="Key performance indicators">
              {loading
                ? Array.from({ length: 4 }, (_, index) => <div className="metric-card skeleton" key={index} />)
                : metrics.map(([key, value], index) => (
                    <article className="metric-card" key={key}>
                      <div className="metric-topline">
                        <span>{formatLabel(key)}</span>
                        <span className={`metric-icon metric-icon-${index + 1}`} aria-hidden="true">
                          {index === 0 ? '↗' : index === 1 ? '◫' : index === 2 ? '◎' : '◇'}
                        </span>
                      </div>
                      <strong>{formatValue(value, key)}</strong>
                      <small>{typeof value === 'object' ? 'Distribution across records' : 'Current operational value'}</small>
                      {typeof value === 'number' && key.includes('percent') && (
                        <span className="progress"><i style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} /></span>
                      )}
                    </article>
                  ))}
            </section>

            <section className="data-panel">
              <div className="panel-heading">
                <div>
                  <h2>Operational details</h2>
                  <p>{data ? `${formatValue(data.summary.returned_records)} of ${formatValue(data.summary.total_records)} records shown` : 'Loading records…'}</p>
                </div>
                <span className="source-label">Source · {data?.view ?? 'connecting'}</span>
              </div>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      {config.columns.map((column) => <th key={column.path}>{column.label}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {loading
                      ? Array.from({ length: 6 }, (_, row) => (
                          <tr className="loading-row" key={row}>
                            {config.columns.map((column) => <td key={column.path}><span /></td>)}
                          </tr>
                        ))
                      : data?.items.slice(0, 12).map((item, rowIndex) => (
                          <tr key={rowIndex}>
                            {config.columns.map((column) => {
                              const value = getValue(item, column.path)
                              return (
                                <td key={column.path}>
                                  {column.tone ? <span className={`status status-${String(value).toLowerCase().replaceAll(' ', '-')}`}>{formatValue(value, column.path)}</span> : formatValue(value, column.path)}
                                </td>
                              )
                            })}
                          </tr>
                        ))}
                    {!loading && data?.items.length === 0 && (
                      <tr><td className="empty-row" colSpan={config.columns.length}>No records are available for this view.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}

export default App
