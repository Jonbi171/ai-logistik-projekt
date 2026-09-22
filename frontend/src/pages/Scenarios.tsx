import { useMediaQuery } from '../components/responsive'
import { useState } from 'react'
import { ArrowRight, FlaskConical, Truck, Boxes } from 'lucide-react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  api,
  type Inventory,
  type InventoryResult,
  type Shipment,
  type ShipmentList,
  type TransportResult,
} from '../api/tower'
import { Panel, State, Note, Metric } from '../components/ui'
import { useData, number, percent } from '../components/data'

export function Scenarios({ reference }: { reference?: string }) {
  const [tab, setTab] = useState<'transport' | 'inventory'>('inventory')
  const inventory = useData<{ items: Inventory[] }>('/tower/inventory')
  const shipments = useData<ShipmentList>('/tower/shipments?limit=100')
  const options = useData<{ carriers: { id: string; name: string }[] }>('/tower/options')
  const isInventory = inventory.data?.items.some((i) => i.id === reference)
  const linked = useData<Shipment>(
    reference && inventory.data && !isInventory ? `/tower/shipments/${reference}` : null,
  )
  const shipmentItems =
    linked.data && !shipments.data?.items.some((s) => s.id === reference)
      ? [linked.data, ...(shipments.data?.items ?? [])]
      : (shipments.data?.items ?? [])
  const isShipment = !!reference && shipmentItems.some((s) => s.id === reference)
  const [chosen, setChosen] = useState(false)
  const active = chosen ? tab : isShipment ? 'transport' : 'inventory'
  const loading = inventory.loading || shipments.loading || options.loading || linked.loading
  const error = inventory.error || shipments.error || options.error || linked.error
  return (
    <>
      <div className="scenario-intro">
        <FlaskConical size={25} />
        <div>
          <h2>Compare planning assumptions</h2>
          <p>
            Adjust demand, receipt timing or shipment details and compare the calculated outcomes.
          </p>
        </div>
      </div>
      <div className="tabs scenario-tabs">
        <button
          className={active === 'inventory' ? 'active' : ''}
          onClick={() => {
            setChosen(true)
            setTab('inventory')
          }}
        >
          <Boxes size={17} />
          Inventory & demand
        </button>
        <button
          className={active === 'transport' ? 'active' : ''}
          onClick={() => {
            setChosen(true)
            setTab('transport')
          }}
        >
          <Truck size={17} />
          Transportation & cost
        </button>
      </div>
      <State
        loading={loading}
        error={error}
        retry={() => {
          inventory.retry()
          shipments.retry()
          options.retry()
          linked.retry()
        }}
      />
      {!loading &&
        !error &&
        inventory.data &&
        shipments.data &&
        options.data &&
        (active === 'inventory' ? (
          <InventoryScenario
            items={inventory.data.items.filter((i) => i.daily_demand !== null)}
            reference={reference}
          />
        ) : (
          <TransportScenario
            items={shipmentItems}
            carriers={options.data.carriers}
            reference={reference}
          />
        ))}
      <Note>
        Scenarios are decision support. They do not place orders, transfer stock, change carriers or
        write to PostgreSQL. Assumptions are shown with each result.
      </Note>
    </>
  )
}

function InventoryScenario({ items, reference }: { items: Inventory[]; reference?: string }) {
  const narrow = useMediaQuery('(max-width: 480px)')
  const [id, setId] = useState(items.find((i) => i.id === reference)?.id ?? items[0]?.id ?? '')
  const row = items.find((i) => i.id === id)!
  const [demand, setDemand] = useState(20),
    [quantity, setQuantity] = useState(500),
    [lead, setLead] = useState(7),
    [safety, setSafety] = useState(row?.safety_stock ?? 0)
  const [result, setResult] = useState<InventoryResult | null>(null),
    [loading, setLoading] = useState(false),
    [error, setError] = useState<string | null>(null)
  const clear = () => {
    setResult(null)
    setError(null)
  }
  async function calculate(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      setResult(
        await api<InventoryResult>('/tower/scenarios/inventory', undefined, {
          inventory_id: id,
          demand_change: demand,
          replenishment: quantity,
          lead_days: lead,
          safety_stock: safety,
        }),
      )
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }
  if (!row) return <Note>No scored inventory positions are available.</Note>
  return (
    <div className="scenario-layout">
      <Panel title="Planning assumptions" subtitle="Change demand, replenishment and timing">
        <form className="scenario-form" onSubmit={calculate}>
          <fieldset disabled={loading}>
            <label>
              Inventory position
              <select
                value={id}
                onChange={(e) => {
                  setId(e.target.value)
                  setSafety(items.find((i) => i.id === e.target.value)!.safety_stock)
                  clear()
                }}
              >
                {items.map((i) => (
                  <option value={i.id} key={i.id}>
                    {i.sku} · {i.location}
                  </option>
                ))}
              </select>
              <span className="selection-summary" aria-hidden="true">
                {row.sku} · {row.location}
              </span>
            </label>
            <label>
              Demand change{' '}
              <strong>
                {demand > 0 ? '+' : ''}
                {demand}%
              </strong>
              <input
                aria-label="Demand change"
                type="range"
                min="-50"
                max="100"
                step="5"
                value={demand}
                onChange={(e) => {
                  setDemand(+e.target.value)
                  clear()
                }}
              />
            </label>
            <label>
              Additional replenishment (units)
              <input
                type="number"
                min="0"
                max="1000000"
                required
                value={quantity}
                onChange={(e) => {
                  setQuantity(+e.target.value)
                  clear()
                }}
              />
            </label>
            <label>
              Receipt on day
              <input
                type="number"
                min="1"
                max="90"
                required
                value={lead}
                onChange={(e) => {
                  setLead(+e.target.value)
                  clear()
                }}
              />
            </label>
            <label>
              Safety stock (units)
              <input
                type="number"
                min="0"
                max="1000000"
                required
                value={safety}
                onChange={(e) => {
                  setSafety(+e.target.value)
                  clear()
                }}
              />
            </label>
            <button className="primary" type="submit">
              {loading ? 'Calculating…' : 'Run inventory scenario'}
              <ArrowRight size={16} />
            </button>
          </fieldset>
        </form>
      </Panel>
      <Panel
        title="Projected inventory impact"
        subtitle={`${row.sku} · available ${number(row.available)} units`}
      >
        {error && (
          <div className="detail-panel">
            <Note warning>{error}</Note>
          </div>
        )}
        {result ? (
          <div className="detail-panel">
            <div className="comparison-head">
              <span>28-day result</span>
              <span>Baseline</span>
              <span>Scenario</span>
            </div>
            {[
              [
                'Closing balance',
                number(result.baseline.projected_balance),
                number(result.scenario.projected_balance),
              ],
              [
                'First shortage',
                result.baseline.shortage_day ? `Day ${result.baseline.shortage_day}` : 'None',
                result.scenario.shortage_day ? `Day ${result.scenario.shortage_day}` : 'None',
              ],
              ['Projected risk', result.baseline.risk, result.scenario.risk],
            ].map(([label, before, after]) => (
              <div className="comparison-row" key={label}>
                <span>{label}</span>
                <strong>{before}</strong>
                <strong>{after}</strong>
              </div>
            ))}
            <div className="chart">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={result.baseline.trajectory.map((p, i) => ({
                    day: p.day,
                    Baseline: p.balance,
                    Scenario: result.scenario.trajectory[i].balance,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 5" vertical={false} />
                  <XAxis dataKey="day" unit="d" />
                  <YAxis width={narrow ? 45 : 60} />
                  <Tooltip formatter={(v) => number(Number(v))} />
                  <ReferenceLine y={0} stroke="var(--danger)" />
                  <Line
                    isAnimationActive={false}
                    dataKey="Baseline"
                    stroke="var(--muted)"
                    dot={false}
                    strokeDasharray="4 3"
                  />
                  <Line
                    isAnimationActive={false}
                    dataKey="Scenario"
                    stroke="var(--olive)"
                    dot={false}
                    strokeWidth={2.5}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <Metric
              label="Additional stock at product unit cost"
              value={`${number(result.incremental_inventory_value)} SEK`}
              detail="Not a landed purchase or transfer cost quote"
            />
            <Note>{result.assumptions}</Note>
          </div>
        ) : (
          <div className="scenario-placeholder">
            <Boxes size={40} />
            <h3>How resilient is this stock position?</h3>
            <p>
              Adjust demand and incoming supply, then run the scenario to compare projected balances
              and shortage timing.
            </p>
          </div>
        )}
      </Panel>
    </div>
  )
}

function TransportScenario({
  items,
  carriers,
  reference,
}: {
  items: Shipment[]
  carriers: { id: string; name: string }[]
  reference?: string
}) {
  const first = items.find((i) => i.id === reference) ?? items[0]
  const [id, setId] = useState(first.id)
  const [distance, setDistance] = useState(first.distance_km),
    [weight, setWeight] = useState(first.total_weight_kg),
    [volume, setVolume] = useState(first.total_volume_m3),
    [mode, setMode] = useState(first.transport_mode),
    [service, setService] = useState(first.service_level),
    [carrier, setCarrier] = useState(first.carrier_id)
  const [result, setResult] = useState<TransportResult | null>(null),
    [loading, setLoading] = useState(false),
    [error, setError] = useState<string | null>(null)
  const clear = () => {
    setResult(null)
    setError(null)
  }
  function select(id: string) {
    const s = items.find((i) => i.id === id)!
    setId(id)
    setDistance(s.distance_km)
    setWeight(s.total_weight_kg)
    setVolume(s.total_volume_m3)
    setMode(s.transport_mode)
    setService(s.service_level)
    setCarrier(s.carrier_id)
    clear()
  }
  async function calculate(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      setResult(
        await api<TransportResult>('/tower/scenarios/transport', undefined, {
          shipment_id: id,
          distance_km: distance,
          total_weight_kg: weight,
          total_volume_m3: volume,
          transport_mode: mode,
          service_level: service,
          carrier_id: carrier,
        }),
      )
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }
  return (
    <div className="scenario-layout">
      <Panel
        title="Transport assumptions"
        subtitle="Use an observed shipment as the starting point"
      >
        <form className="scenario-form" onSubmit={calculate}>
          <fieldset disabled={loading}>
            <label>
              Baseline shipment
              <select value={id} onChange={(e) => select(e.target.value)}>
                {items.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.shipment_number} · {s.carrier}
                  </option>
                ))}
              </select>
              <span className="selection-summary" aria-hidden="true">
                {items.find((item) => item.id === id)?.shipment_number} ·{' '}
                {items.find((item) => item.id === id)?.carrier}
              </span>
            </label>
            {[
              { label: 'Distance (km)', value: distance, set: setDistance, max: 30000 },
              { label: 'Weight (kg)', value: weight, set: setWeight, max: 100000 },
              { label: 'Volume (m³)', value: volume, set: setVolume, max: 1000 },
            ].map((f) => (
              <label key={f.label}>
                {f.label}
                <input
                  type="number"
                  min="0.01"
                  max={f.max}
                  step="any"
                  required
                  value={f.value}
                  onChange={(e) => {
                    f.set(+e.target.value)
                    clear()
                  }}
                />
              </label>
            ))}
            <div className="form-pair">
              <label>
                Mode
                <select
                  value={mode}
                  onChange={(e) => {
                    setMode(e.target.value)
                    clear()
                  }}
                >
                  {['ROAD', 'AIR', 'OCEAN'].map((x) => (
                    <option key={x}>{x}</option>
                  ))}
                </select>
              </label>
              <label>
                Service
                <select
                  value={service}
                  onChange={(e) => {
                    setService(e.target.value)
                    clear()
                  }}
                >
                  {['STANDARD', 'EXPRESS'].map((x) => (
                    <option key={x}>{x}</option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              Carrier
              <select
                value={carrier}
                onChange={(e) => {
                  setCarrier(e.target.value)
                  clear()
                }}
              >
                {carriers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              <span className="selection-summary" aria-hidden="true">
                {carriers.find((item) => item.id === carrier)?.name}
              </span>
            </label>
            <button className="primary" type="submit">
              {loading ? 'Predicting…' : 'Run transport scenario'}
              <ArrowRight size={16} />
            </button>
          </fieldset>
        </form>
      </Panel>
      <Panel
        title="Cost & service tradeoff"
        subtitle="Model estimates using your proposed shipment attributes"
      >
        {error && (
          <div className="detail-panel">
            <Note warning>{error}</Note>
          </div>
        )}
        {result ? (
          <div className="detail-panel">
            <div className="cost-result">
              <span>PREDICTED FREIGHT COST</span>
              <strong>
                {number(result.scenario.cost)} <small>SEK</small>
              </strong>
              <p>
                {result.scenario.cost - result.baseline.cost >= 0 ? '+' : ''}
                {number(result.scenario.cost - result.baseline.cost)} SEK versus baseline model
                estimate
              </p>
            </div>
            <div className="comparison-head">
              <span>Decision metric</span>
              <span>Baseline</span>
              <span>Scenario</span>
            </div>
            {[
              [
                'Cost / km',
                `${number(result.baseline.cost_per_km, 2)} SEK`,
                `${number(result.scenario.cost_per_km, 2)} SEK`,
              ],
              [
                'Late probability',
                percent(result.baseline.late_probability),
                percent(result.scenario.late_probability),
              ],
              [
                'Predicted delay',
                `${number(result.baseline.delay_hours, 1)} h`,
                `${number(result.scenario.delay_hours, 1)} h`,
              ],
            ].map(([label, before, after]) => (
              <div className="comparison-row" key={label}>
                <span>{label}</span>
                <strong>{before}</strong>
                <strong>{after}</strong>
              </div>
            ))}
            <p className="footnote">
              Historical mean for {number(result.scenario.comparable_count)} shipments with the same
              mode and service: {number(result.scenario.historical_average)} SEK. Load and distance
              are not matched.
            </p>
            {result.warnings.map((w) => (
              <Note key={w} warning>
                {w}
              </Note>
            ))}
            <Note>{result.assumptions}</Note>
          </div>
        ) : (
          <div className="scenario-placeholder">
            <Truck size={40} />
            <h3>What changes the cost of service?</h3>
            <p>
              Adjust the shipment, then compare predicted freight cost, cost per kilometre and
              estimated delivery risk.
            </p>
          </div>
        )}
      </Panel>
    </div>
  )
}
