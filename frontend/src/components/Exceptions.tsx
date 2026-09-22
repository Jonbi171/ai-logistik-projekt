import { useState } from 'react'
import { ArrowRight, Check, ChevronDown } from 'lucide-react'
import type { Exception, Page } from '../api/tower'
import { Badge, Empty } from './ui'

export function Exceptions({
  items,
  navigate,
}: {
  items: Exception[]
  navigate: (page: Page, reference?: string) => void
}) {
  const [filter, setFilter] = useState('All')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [reviewed, setReviewed] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem('tower-reviewed') ?? '[]')
    } catch {
      return []
    }
  })
  const visible = items.filter((e) => filter === 'All' || e.type === filter).slice(0, 12)
  function review(id: string) {
    const next = reviewed.includes(id) ? reviewed.filter((x) => x !== id) : [...reviewed, id]
    setReviewed(next)
    localStorage.setItem('tower-reviewed', JSON.stringify(next))
  }
  return (
    <>
      <div className="tabs">
        {['All', 'Transportation', 'Inventory', 'Anomaly', 'Supplier'].map((t) => (
          <button className={filter === t ? 'active' : ''} onClick={() => setFilter(t)} key={t}>
            {t}
          </button>
        ))}
      </div>
      <div className="exception-list">
        {visible.map((item) => (
          <article key={item.id} className={`exception ${expanded === item.id ? 'expanded' : ''}`}>
            <button
              className="exception-main"
              aria-expanded={expanded === item.id}
              onClick={() => setExpanded(expanded === item.id ? null : item.id)}
            >
              <span className={`exception-dot ${item.severity.toLowerCase()}`} />
              <div className="exception-copy">
                <div>
                  <strong>{item.object}</strong>
                  <span className="micro-label">
                    {item.type}
                    {item.replay ? ' · Replay' : ' · Projection'}
                  </span>
                </div>
                <p>{item.trigger}</p>
              </div>
              <Badge risk={item.severity} />
              <ChevronDown size={16} />
            </button>
            {expanded === item.id && (
              <div className="exception-detail">
                <div className="decision-chain">
                  <div>
                    <small>AFFECTED KPI</small>
                    <strong>{item.kpi}</strong>
                  </div>
                  <ArrowRight size={18} />
                  <div>
                    <small>BUSINESS IMPACT</small>
                    <strong>{item.impact}</strong>
                  </div>
                  <ArrowRight size={18} />
                  <div>
                    <small>RECOMMENDED RESPONSE</small>
                    <strong>{item.action}</strong>
                  </div>
                </div>
                <p>{item.expected_impact}</p>
                <div className="actions">
                  <button className="primary" onClick={() => navigate(item.page, item.reference)}>
                    Inspect evidence <ArrowRight size={15} />
                  </button>
                  <button onClick={() => review(item.id)}>
                    <Check size={15} />
                    {reviewed.includes(item.id) ? 'Reviewed · undo' : 'Mark reviewed'}
                  </button>
                  <small>
                    Review state is saved in this browser. No operational action is executed.
                  </small>
                </div>
              </div>
            )}
          </article>
        ))}
      </div>
      {!visible.length && <Empty text="No exceptions in this category." />}
      <p className="footnote">
        Showing {visible.length} of{' '}
        {items.filter((e) => filter === 'All' || e.type === filter).length} signals, ranked by rule
        severity and model score. Independent recommendations require planner review.
      </p>
    </>
  )
}
