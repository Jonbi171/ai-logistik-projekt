import { useState } from 'react'
import { ArrowRight, Search } from 'lucide-react'
import type { Inventory as Position, Page } from '../api/tower'
import { Badge, TableScroll, Panel, State, Note, Metric, Empty } from '../components/ui'
import { useData, number } from '../components/data'

export function Inventory({
  reference,
  navigate,
}: {
  reference?: string
  navigate: (p: Page, reference?: string) => void
}) {
  const result = useData<{ items: Position[] }>('/tower/inventory')
  const [q, setQ] = useState(''),
    [risk, setRisk] = useState(''),
    [selected, setSelected] = useState(reference ?? '')
  const items = result.data?.items ?? []
  const rows = items.filter(
    (r) =>
      `${r.sku} ${r.product} ${r.location}`.toLowerCase().includes(q.toLowerCase()) &&
      (!risk || r.risk === risk),
  )
  const detail = items.find((r) => r.id === selected) ?? rows[0]
  return (
    <>
      <Note>
        Forecast-based projection, not a stockout classifier. Demand is allocated using each
        warehouse’s recent sales share. Only confirmed, dated incoming quantities are counted;
        component demand remains unscored.
      </Note>
      <State {...result} />
      {result.data && (
        <>
          <div className="metrics-row standalone">
            <Metric
              label="Projected shortage positions"
              value={items.filter((i) => i.risk === 'High').length}
              detail="Negative balance within 28 days"
            />
            <Metric
              label="Inventory value"
              value={`${number(items.reduce((s, i) => s + i.inventory_value, 0))} SEK`}
              detail="On-hand × product unit cost"
            />
            <Metric
              label="Excess-stock positions"
              value={items.filter((i) => i.excess).length}
              detail="Above 56 days of demand + safety stock"
            />
            <Metric
              label="Forecast coverage"
              value={`${items.filter((i) => i.risk !== 'Not scored').length} / ${items.length}`}
              detail="SKU-location positions scored"
            />
          </div>
          <Panel
            title="Inventory exposure"
            subtitle="Where does the latest demand forecast put supply under pressure?"
          >
            <div className="filters">
              <label className="search">
                <Search size={16} />
                <input
                  aria-label="Search inventory"
                  placeholder="Find a SKU, product or warehouse…"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                />
              </label>
              <select
                aria-label="Inventory risk"
                value={risk}
                onChange={(e) => setRisk(e.target.value)}
              >
                <option value="">All risk levels</option>
                {['High', 'Medium', 'Low', 'Not scored'].map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </div>
            <TableScroll label="Inventory positions">
              <table>
                <thead>
                  <tr>
                    <th>Product / location</th>
                    <th>Available</th>
                    <th>28-day demand</th>
                    <th>Confirmed inbound</th>
                    <th>Days of supply</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr className={detail?.id === r.id ? 'selected' : ''} key={r.id}>
                      <td>
                        <button className="table-link" onClick={() => setSelected(r.id)}>
                          {r.sku}
                        </button>
                        <small>{r.location}</small>
                      </td>
                      <td>
                        {number(r.available)}
                        <small>Safety stock {number(r.safety_stock)}</small>
                      </td>
                      <td>{number(r.forecast_demand)}</td>
                      <td>{number(r.incoming)}</td>
                      <td>
                        {number(r.days_of_supply, 1)}
                        {r.excess && <small className="amber-text">Excess coverage</small>}
                      </td>
                      <td>
                        <Badge risk={r.risk} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableScroll>
            {!rows.length && <Empty />}
          </Panel>
          {detail && (
            <Panel
              title={`${detail.sku} · planning decision`}
              subtitle={`${detail.product} / ${detail.location}`}
            >
              <div className="detail-panel">
                <div className="metrics-row">
                  <Metric
                    label="Projected closing balance"
                    value={number(detail.projected_balance)}
                    detail="Units at day 28"
                  />
                  <Metric
                    label="First shortage"
                    value={detail.shortage_day ? `Day ${detail.shortage_day}` : 'None projected'}
                  />
                  <Metric label="Reorder point" value={number(detail.reorder_point)} />
                </div>
                <div className="recommendation">
                  <h3>{detail.action}</h3>
                  {detail.transfer && (
                    <p>
                      Candidate transfer: {number(detail.transfer.quantity)} units.
                      Immediate-receipt coverage would change from{' '}
                      {number(detail.transfer.days_before, 1)} to{' '}
                      {number(detail.transfer.days_after, 1)} days. Transfer time, cost, capacity,
                      and competing recommendations still require review.
                    </p>
                  )}
                  <div className="actions">
                    <button
                      className="primary"
                      disabled={detail.daily_demand === null}
                      onClick={() => navigate('Scenario Analysis', detail.id)}
                    >
                      Stress-test this position <ArrowRight size={16} />
                    </button>
                    <button onClick={() => navigate('Demand', detail.product_id)}>
                      Inspect demand forecast
                    </button>
                  </div>
                </div>
                <p className="footnote">
                  {detail.method} Forecast origin: {detail.forecast_origin ?? 'unavailable'};
                  inventory snapshot: {detail.as_of.slice(0, 10)}. The latest demand level is
                  carried forward to the snapshot date.
                </p>
              </div>
            </Panel>
          )}
        </>
      )}
    </>
  )
}
