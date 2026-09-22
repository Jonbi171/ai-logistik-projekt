import { useMediaQuery } from '../components/responsive'
import { useState } from 'react'
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from 'recharts'
import type { Forecast, Inventory, Page } from '../api/tower'
import { TableScroll, Panel, State, Note, Metric, Badge } from '../components/ui'
import { useData, number, percent } from '../components/data'

export function Demand({
  reference,
  navigate,
}: {
  reference?: string
  navigate: (page: Page, reference?: string) => void
}) {
  const result = useData<{ items: Forecast[] }>('/tower/demand')
  const inventory = useData<{ items: Inventory[] }>('/tower/inventory')
  const narrow = useMediaQuery('(max-width: 480px)')
  const [sku, setSku] = useState(reference ?? '')
  const f = result.data?.items.find((r) => r.product_id === sku) ?? result.data?.items[0]
  return (
    <>
      <State {...result} />
      {f && (
        <>
          <Panel
            title="Demand planning"
            subtitle="Turn customer orders into a four-week supply requirement"
            action={
              <>
                <select
                  aria-label="Select demand product"
                  value={f.product_id}
                  onChange={(e) => setSku(e.target.value)}
                >
                  {result.data!.items.map((i) => (
                    <option value={i.product_id} key={i.product_id}>
                      {i.sku} · {i.product}
                    </option>
                  ))}
                </select>
                <span className="selection-summary" aria-hidden="true">
                  {f.sku} · {f.product}
                </span>
              </>
            }
          >
            <div className="detail-panel">
              <div className="metrics-row">
                <Metric
                  label="Next 4 weeks"
                  value={number(f.next_4_weeks)}
                  detail="Forecast units, all warehouses"
                />
                <Metric
                  label="Holdout WAPE"
                  value={percent(f.metrics.wape)}
                  detail="Final 8 completed weeks"
                />
                <Metric
                  label="Holdout MAE"
                  value={number(f.metrics.mae, 1)}
                  detail="Units / week"
                />
                <Metric
                  label="Forecast bias"
                  value={number(f.metrics.bias, 1)}
                  detail="Positive = over-forecast"
                />
              </div>
              <div className="chart tall">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={[...f.history.slice(-32), ...f.future]}
                    margin={{ top: 15, right: narrow ? 8 : 20, left: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 5" vertical={false} />
                    <XAxis
                      dataKey="week"
                      tickFormatter={(v) => String(v).slice(5)}
                      minTickGap={25}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis width={narrow ? 40 : 60} axisLine={false} tickLine={false} />
                    <Tooltip formatter={(v) => number(Number(v), 1)} />
                    <ReferenceLine
                      x={f.future[0].week}
                      stroke="var(--muted)"
                      strokeDasharray="4 4"
                      label={{
                        value: 'Forecast',
                        position: 'insideTopRight',
                        fill: 'var(--muted)',
                        fontSize: 11,
                      }}
                    />
                    <Line
                      isAnimationActive={false}
                      type="monotone"
                      dataKey="actual"
                      name="Historical demand"
                      stroke="var(--ink)"
                      dot={false}
                      strokeWidth={2}
                    />
                    <Line
                      isAnimationActive={false}
                      dataKey="backtest"
                      name="Holdout prediction"
                      stroke="var(--rust)"
                      strokeDasharray="4 3"
                      dot={false}
                    />
                    <Line
                      isAnimationActive={false}
                      dataKey="forecast"
                      name="Future forecast"
                      stroke="var(--olive)"
                      strokeWidth={3}
                      dot={{ r: 4 }}
                    />
                    <Line
                      isAnimationActive={false}
                      dataKey="lower"
                      name="Approx. lower range"
                      stroke="var(--olive-light)"
                      strokeDasharray="3 3"
                      dot={false}
                    />
                    <Line
                      isAnimationActive={false}
                      dataKey="upper"
                      name="Approx. upper range"
                      stroke="var(--olive-light)"
                      strokeDasharray="3 3"
                      dot={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <div className="chart-legend">
                <span>
                  <i style={{ background: 'var(--ink)' }} />
                  Actual demand
                </span>
                <span>
                  <i style={{ background: 'var(--rust)' }} />
                  Holdout prediction
                </span>
                <span>
                  <i style={{ background: 'var(--olive)' }} />
                  Next 4 weeks
                </span>
                <span>
                  <i style={{ background: 'var(--olive-light)' }} />
                  Approximate 80% residual range
                </span>
              </div>
            </div>
          </Panel>
          <div className="two-col">
            <Panel title="Forecast method" subtitle={f.model}>
              <div className="detail-panel">
                <p>{f.methodology}</p>
                <div className="metrics-row">
                  <Metric label="History" value={`${f.weeks} weeks`} />
                  <Metric label="RMSE" value={number(f.metrics.rmse, 1)} />
                  <Metric
                    label="Baseline WAPE"
                    value={percent(f.baseline.wape)}
                    detail="4-week moving average"
                  />
                </div>
              </div>
            </Panel>
            <Panel title="From forecast to action" subtitle="How this changes inventory decisions">
              <State {...inventory} />
              <TableScroll label="Inventory by warehouse">
                <table>
                  <thead>
                    <tr>
                      <th>Recorded position</th>
                      <th>Available + inbound</th>
                      <th>28-day demand</th>
                      <th>Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {inventory.data?.items
                      .filter((i) => i.product_id === f.product_id)
                      .map((i) => (
                        <tr key={i.id}>
                          <td>
                            <button
                              className="table-link"
                              onClick={() => navigate('Inventory', i.id)}
                            >
                              {i.location.replace(' Regional Warehouse', '')}
                            </button>
                          </td>
                          <td>{number(i.available + i.incoming)}</td>
                          <td>{number(i.forecast_demand)}</td>
                          <td>
                            <Badge risk={i.risk} />
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </TableScroll>
              <p className="footnote">
                Compare the forecast with each recorded inventory position. Select a warehouse to
                inspect shortage timing, safety stock, and a replenishment scenario. Missing
                locations are not assumed to have zero stock.
              </p>
            </Panel>
          </div>
          <Note>
            The forecast begins after the latest completed sales week, not today. The inventory page
            carries this demand level forward to the later balance snapshot. Forecast error and
            stale demand history remain material planning limitations.
          </Note>
        </>
      )}
    </>
  )
}
