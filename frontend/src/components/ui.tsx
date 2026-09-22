import { useId, useState, type ReactNode } from 'react'
import { ArrowUpRight, Info, RefreshCw, TriangleAlert } from 'lucide-react'
import { type KPI, type Risk } from '../api/tower'
import { number } from './data'

export function State({
  loading,
  error,
  retry,
}: {
  loading: boolean
  error: string | null
  retry?: () => void
}) {
  if (error)
    return (
      <div className="empty error" role="alert">
        <TriangleAlert />
        <h3>Unable to load this view</h3>
        <p>{error}</p>
        <button onClick={retry}>
          <RefreshCw size={15} /> Try again
        </button>
      </div>
    )
  return loading ? (
    <div className="skeleton-grid" aria-label="Loading analytics" aria-busy="true">
      {[0, 1, 2, 3].map((i) => (
        <div className="skeleton" key={i} />
      ))}
    </div>
  ) : null
}
export function Badge({ risk }: { risk: Risk | string }) {
  return (
    <span className={`badge ${risk.toLowerCase().replaceAll(' ', '-')}`}>
      <i />
      {risk}
    </span>
  )
}
export function Panel({
  title,
  subtitle,
  action,
  children,
  className = '',
}: {
  title: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}
export function KPIGrid({ items }: { items: KPI[] }) {
  return (
    <div className="kpi-grid">
      {items.map((k) => (
        <article className={`kpi ${k.tone}`} key={k.label}>
          <div className="kpi-label">
            {k.label}
            <Definition label={k.label} text={k.definition} />
          </div>
          <div className="kpi-value">
            {k.unit === 'SEK' && (k.value ?? 0) >= 1000000
              ? `${number((k.value ?? 0) / 1000000, 2)}m`
              : number(k.value, k.unit === '%' || k.unit === 'h' ? 1 : 0)}
            <span>{k.unit}</span>
          </div>
          <p>{k.detail}</p>
        </article>
      ))}
    </div>
  )
}
function Definition({ label, text }: { label: string; text: string }) {
  const [open, setOpen] = useState(false)
  const id = useId()
  return (
    <span className="definition">
      <button
        className="icon-button"
        aria-label={`About ${label}`}
        aria-expanded={open}
        aria-describedby={open ? id : undefined}
        onClick={() => setOpen(!open)}
        onBlur={() => setOpen(false)}
        onKeyDown={(event) => {
          if (event.key === 'Escape') setOpen(false)
        }}
      >
        <Info size={14} />
      </button>
      {open && (
        <span id={id} role="tooltip">
          {text}
        </span>
      )}
    </span>
  )
}

export function TableScroll({ label, children }: { label: string; children: ReactNode }) {
  const hint = useId()
  return (
    <div className="table-region">
      <p id={hint} className="table-scroll-hint">
        Scroll horizontally to see all columns.
      </p>
      <div
        className="table-wrap"
        role="region"
        aria-label={label}
        aria-describedby={hint}
        tabIndex={0}
      >
        {children}
      </div>
    </div>
  )
}
export function Note({ children, warning = false }: { children: ReactNode; warning?: boolean }) {
  return (
    <div className={`note ${warning ? 'warning' : ''}`}>
      <Info size={17} />
      <div>{children}</div>
    </div>
  )
}
export function Empty({ text = 'No results match these filters.' }: { text?: string }) {
  return (
    <div className="empty">
      <h3>{text}</h3>
      <p>Adjust the filters to explore more of the dataset.</p>
    </div>
  )
}
export function Metric({
  label,
  value,
  detail,
}: {
  label: string
  value: ReactNode
  detail?: string
}) {
  return (
    <div className="mini-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </div>
  )
}
export function LinkButton({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return (
    <button className="text-button" onClick={onClick}>
      {children}
      <ArrowUpRight size={15} />
    </button>
  )
}
