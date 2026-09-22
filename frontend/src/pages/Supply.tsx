import { useMediaQuery } from '../components/responsive'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from 'recharts'
import type { Supplier, Production as ProductionData } from '../api/tower'
import { Badge, TableScroll, Panel, State, Note, Metric } from '../components/ui'
import { useData, number, percent } from '../components/data'

export function Suppliers() {
  const narrow = useMediaQuery('(max-width: 480px)')
  const result = useData<{ items: Supplier[] }>('/tower/suppliers')
  return (
    <>
      <Note warning>
        Supplier scores average predictions on completed, held-out purchase orders. This baseline
        has near-random ranking performance. Use the observed service and quality KPIs as primary
        evidence.
      </Note>
      <State {...result} />
      {result.data && (
        <>
          <Panel
            title="Supplier reliability"
            subtitle="Historical delivery, quantity and quality performance"
          >
            <TableScroll label="Supplier performance">
              <table>
                <thead>
                  <tr>
                    <th>Supplier</th>
                    <th>On-time delivery</th>
                    <th>Lead time</th>
                    <th>Fill rate</th>
                    <th>Rejection rate</th>
                    <th>Replay late score</th>
                  </tr>
                </thead>
                <tbody>
                  {result.data.items.map((s) => (
                    <tr key={s.id}>
                      <td>
                        <strong>{s.name}</strong>
                        <small>
                          {s.country} · {number(s.orders)} completed orders
                        </small>
                      </td>
                      <td>{number(s.on_time, 1)}%</td>
                      <td>{number(s.lead_days, 1)} days</td>
                      <td>{number(s.fill_rate, 1)}%</td>
                      <td>{number(s.rejection_rate, 2)}%</td>
                      <td>
                        {percent(s.late_probability)} <Badge risk={s.risk} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableScroll>
            <p className="footnote">
              OTD: actual ≤ requested delivery date. Fill rate: received ÷ ordered quantity.
              Rejection rate: rejected ÷ received quantity.
            </p>
          </Panel>
          <div className="two-col">
            <Panel
              title="Delivery reliability by supplier"
              subtitle="Share received by the original requested date"
            >
              <div className="chart tall">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={result.data.items.map((s) => ({
                      ...s,
                      short: s.name.split(' ').slice(0, 2).join(' '),
                    }))}
                    layout="vertical"
                    margin={{ left: narrow ? 0 : 20, right: narrow ? 12 : 30 }}
                  >
                    <CartesianGrid horizontal={false} strokeDasharray="3 5" />
                    <XAxis type="number" domain={[0, 100]} unit="%" />
                    <YAxis
                      type="category"
                      dataKey="short"
                      width={narrow ? 100 : 120}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip formatter={(v) => `${number(Number(v), 1)}%`} />
                    <Bar
                      isAnimationActive={false}
                      dataKey="on_time"
                      name="On-time delivery"
                      fill="var(--olive)"
                      radius={[0, 4, 4, 0]}
                      barSize={24}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Panel>
            <Panel
              title="Sourcing decision support"
              subtitle="Use evidence to review replenishment policy"
            >
              <div className="detail-panel">
                <div className="recommendation">
                  <h3>Review lead-time buffers before urgent demand</h3>
                  <p>
                    Compare requested-date reliability, observed lead time and rejection rate.
                    Consider earlier ordering and check approved alternative suppliers.
                  </p>
                </div>
                <Note>
                  Alternative supplier capacity, product approval and commercial terms must be
                  checked before changing source. A high experimental model score alone is not a
                  reason to switch suppliers.
                </Note>
              </div>
            </Panel>
          </div>
        </>
      )}
    </>
  )
}

export function Production() {
  const narrow = useMediaQuery('(max-width: 480px)')
  const result = useData<ProductionData>('/tower/production')
  const p = result.data
  return (
    <>
      <State {...result} />
      {p && (
        <>
          <div className="metrics-row standalone">
            <Metric label="Capacity utilization" value={`${number(p.utilization, 1)}%`} />
            <Metric label="Plan attainment" value={`${number(p.plan_attainment, 1)}%`} />
            <Metric label="Scrap / produced" value={`${number(p.scrap_rate, 2)}%`} />
            <Metric label="Late completions" value={`${number(p.late_rate, 1)}%`} />
          </div>
          <Panel
            title="Production capacity"
            subtitle="Historical actual output against planned capacity"
          >
            <div className="chart tall">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={p.monthly.slice(-12)}
                  margin={{ top: 15, left: 0, right: narrow ? 8 : 20 }}
                >
                  <CartesianGrid vertical={false} strokeDasharray="3 5" />
                  <XAxis dataKey="month" tickFormatter={(v) => String(v).slice(2)} />
                  <YAxis
                    width={narrow ? 40 : 60}
                    tickFormatter={(v) => `${number(Number(v) / 1000)}k`}
                  />
                  <Tooltip formatter={(v) => number(Number(v))} />
                  <Legend />
                  <Bar
                    isAnimationActive={false}
                    dataKey="planned"
                    name="Planned units"
                    fill="var(--rule)"
                    radius={[3, 3, 0, 0]}
                  />
                  <Bar
                    isAnimationActive={false}
                    dataKey="actual"
                    name="Actual units"
                    fill="var(--olive)"
                    radius={[3, 3, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Panel>
          <Note>
            {p.definition} Recorded downtime: {number(p.downtime_hours, 1)} hours.
          </Note>
          <Panel title="Recent production orders" subtitle="Completed manufacturing history">
            <TableScroll label="Production orders">
              <table>
                <thead>
                  <tr>
                    <th>Order / plant</th>
                    <th>Product</th>
                    <th>Planned</th>
                    <th>Produced</th>
                    <th>Scrapped</th>
                  </tr>
                </thead>
                <tbody>
                  {p.orders.slice(0, 30).map((o) => (
                    <tr key={o.production_order_number}>
                      <td>
                        <strong>{o.production_order_number}</strong>
                        <small>{o.plant}</small>
                      </td>
                      <td>{o.product}</td>
                      <td>{number(o.planned_quantity)}</td>
                      <td>{number(o.produced_quantity)}</td>
                      <td>{number(o.scrapped_quantity)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableScroll>
          </Panel>
        </>
      )}
    </>
  )
}
