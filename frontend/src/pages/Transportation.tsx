import { useCallback, useState } from 'react'
import { ArrowRight, Search, X } from 'lucide-react'
import type { ShipmentList, Shipment, Page } from '../api/tower'
import { Badge, TableScroll, Panel, State, Note, Metric, Empty } from '../components/ui'
import { useData, number, percent, date } from '../components/data'
import { useModal } from '../components/responsive'

export function Transportation({
  reference,
  navigate,
}: {
  reference?: string
  navigate: (p: Page, reference?: string) => void
}) {
  const [query, setQuery] = useState(''),
    [risk, setRisk] = useState(''),
    [mode, setMode] = useState(''),
    [anomalies, setAnomalies] = useState(false),
    [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState<Shipment | null>(null)
  const params = new URLSearchParams({
    q: query,
    risk,
    mode,
    anomalies: String(anomalies),
    offset: String(offset),
    limit: '50',
  })
  const result = useData<ShipmentList>(`/tower/shipments?${params}`)
  const linked = useData<Shipment>(reference ? `/tower/shipments/${reference}` : null)
  const detail = selected ?? linked.data ?? result.data?.items.find((s) => s.id === reference)
  const closeDetail = useCallback(() => {
    setSelected(null)
    navigate('Transportation')
  }, [navigate])
  const drawerRef = useModal(!!detail, closeDetail)
  return (
    <>
      <Note warning>
        Historical replay of {number(result.data?.total)} matching shipments from the held-out
        period. All source shipments are delivered. Scores use pre-departure features; actual
        outcomes are shown for comparison. The delay classifier has limited ranking power.
      </Note>
      {linked.error && <Note warning>{linked.error}</Note>}
      <Panel
        title="Shipment risk monitor"
        subtitle="Understand delivery exposure before the planned departure"
      >
        <div className="filters">
          <label className="search">
            <Search size={16} />
            <input
              aria-label="Search shipments"
              placeholder="Shipment, carrier, route or order…"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                setOffset(0)
              }}
            />
          </label>
          <select
            aria-label="Risk level"
            value={risk}
            onChange={(e) => {
              setRisk(e.target.value)
              setOffset(0)
            }}
          >
            <option value="">All risk levels</option>
            {['High', 'Medium', 'Low'].map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
          <select
            aria-label="Transport mode"
            value={mode}
            onChange={(e) => {
              setMode(e.target.value)
              setOffset(0)
            }}
          >
            <option value="">All modes</option>
            {['ROAD', 'AIR', 'OCEAN'].map((m) => (
              <option key={m}>{m}</option>
            ))}
          </select>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={anomalies}
              onChange={(e) => {
                setAnomalies(e.target.checked)
                setOffset(0)
              }}
            />
            Anomalies only
          </label>
        </div>
        <State {...result} />
        {result.data && (
          <>
            <TableScroll label="Shipments">
              <table>
                <thead>
                  <tr>
                    <th>Shipment / carrier</th>
                    <th>Route</th>
                    <th>Late probability</th>
                    <th>Predicted delay</th>
                    <th>Risk</th>
                    <th>Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {result.data.items.map((s) => (
                    <tr key={s.id}>
                      <td>
                        <button className="table-link" onClick={() => setSelected(s)}>
                          {s.shipment_number}
                        </button>
                        <small>{s.carrier}</small>
                      </td>
                      <td>
                        {s.origin.replace(' Regional Warehouse', '')}
                        <small>→ {s.destination.replace(' Main Site', '')}</small>
                      </td>
                      <td>
                        <div className="probability">
                          <span>{percent(s.late_probability)}</span>
                          <i style={{ width: `${s.late_probability * 100}%` }} />
                        </div>
                      </td>
                      <td>
                        +{number(s.predicted_delay, 1)} h
                        <small>
                          {s.transport_mode} · {s.service_level}
                        </small>
                      </td>
                      <td>
                        <Badge risk={s.risk} />
                      </td>
                      <td>
                        <button
                          className="icon-button"
                          aria-label={`Inspect ${s.shipment_number}`}
                          onClick={() => setSelected(s)}
                        >
                          <ArrowRight size={17} />
                        </button>
                        {s.anomaly && (
                          <span className="anomaly-dot" title="Isolation Forest anomaly" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableScroll>
            {!result.data.items.length && <Empty />}
            <div className="pagination">
              <span>
                {number(result.data.total ? offset + 1 : 0)}–
                {number(Math.min(offset + 50, result.data.total))} of {number(result.data.total)} ·
                High ≥50%, medium ≥30%
              </span>
              <button disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 50))}>
                Previous
              </button>
              <button
                disabled={offset + 50 >= result.data.total}
                onClick={() => setOffset(offset + 50)}
              >
                Next
              </button>
            </div>
          </>
        )}
      </Panel>
      {detail && (
        <div className="drawer-backdrop" onClick={closeDetail}>
          <aside
            ref={drawerRef}
            className="drawer"
            role="dialog"
            aria-modal="true"
            aria-label={`Shipment ${detail.shipment_number}`}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              data-modal-close
              className="drawer-close icon-button"
              aria-label="Close shipment"
              onClick={closeDetail}
            >
              <X size={20} />
            </button>
            <span className="eyebrow">SHIPMENT INTELLIGENCE · REPLAY</span>
            <h2>{detail.shipment_number}</h2>
            <p>
              {detail.origin}
              <br />→ {detail.destination}
            </p>
            <div className="metrics-row">
              <Metric label="Late probability" value={percent(detail.late_probability)} />
              <Metric label="Predicted delay" value={`+${number(detail.predicted_delay, 1)} h`} />
            </div>
            <Note warning>
              Uncalibrated experimental score with weak holdout ranking. Review the measured metrics
              in AI / ML Insights before relying on delivery probabilities.
            </Note>
            <h3>Prediction & observed outcome</h3>
            <dl className="detail-list">
              <div>
                <dt>Planned arrival</dt>
                <dd>{date(detail.planned_arrival_at)}</dd>
              </div>
              <div>
                <dt>Predicted ETA</dt>
                <dd>{new Date(detail.predicted_eta).toLocaleString('en-GB')}</dd>
              </div>
              <div>
                <dt>Actual arrival</dt>
                <dd>{new Date(detail.actual_arrival_at).toLocaleString('en-GB')}</dd>
              </div>
              <div>
                <dt>Observed positive delay</dt>
                <dd>{number(detail.target_delay, 1)} h</dd>
              </div>
              <div>
                <dt>Linked order(s)</dt>
                <dd>{detail.orders}</dd>
              </div>
              <div>
                <dt>Order priority</dt>
                <dd>{detail.priority}</dd>
              </div>
              <div>
                <dt>Actual / predicted freight</dt>
                <dd>
                  {number(detail.freight_cost_sek)} / {number(detail.predicted_cost)} SEK
                </dd>
              </div>
            </dl>
            <h3>Planning context</h3>
            <div className="chips">
              {detail.context.map((c) => (
                <span key={c}>{c}</span>
              ))}
            </div>
            <p className="footnote">
              Input context, not individual causal attribution. Global feature importance is
              available in AI / ML Insights.
            </p>
            {detail.anomaly && (
              <Note>
                This shipment is unusual. Cost/km is {number(detail.cost_ratio, 2)}× the median for
                its mode and service. Check route and load before drawing conclusions.
              </Note>
            )}
            <div className="recommendation">
              <span className="eyebrow">RECOMMENDED RESPONSE</span>
              <h3>Review carrier and delivery commitment</h3>
              <p>
                Compare transport choices, then assess cost and service tradeoffs with the planner.
              </p>
              <button className="primary" onClick={() => navigate('Scenario Analysis', detail.id)}>
                Compare a scenario <ArrowRight size={16} />
              </button>
            </div>
          </aside>
        </div>
      )}
    </>
  )
}
