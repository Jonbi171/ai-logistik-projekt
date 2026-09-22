import { useState } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ArrowRight, Boxes, CircleDot, ScanLine, Truck } from 'lucide-react'
import type { Overview as OverviewData, Exception, Page } from '../api/tower'
import { KPIGrid, Panel, LinkButton, Note } from '../components/ui'
import { number } from '../components/data'
import { Exceptions } from '../components/Exceptions'

export function Overview({
  data,
  exceptions,
  navigate,
}: {
  data: OverviewData
  exceptions: Exception[]
  navigate: (p: Page, reference?: string) => void
}) {
  const [period, setPeriod] = useState(12)
  const nodes = data.locations.filter((l) => l.longitude < 35)
  const position = (id: string) => {
    const l = nodes.find((n) => n.id === id)
    return l ? { x: 45 + (l.longitude - 3) * 18, y: 320 - (l.latitude - 47) * 16 } : null
  }
  return (
    <div className="overview-layout">
      <div className="overview-banner">
        <div>
          <span className="eyebrow">01 / Operations brief</span>
          <h2>Delivery & stock exposure</h2>
          <p>
            Review historical delivery results, then check where forecast demand exceeds available
            stock.
          </p>
        </div>
        <button onClick={() => navigate('Scenario Analysis')}>
          Test a planning assumption <ArrowRight size={17} />
        </button>
      </div>
      <KPIGrid items={data.kpis} />
      <div className="intelligence-strip">
        <div className="intelligence-label">
          <ScanLine size={20} />
          <div>
            <strong>For review</strong>
            <small>Historical scores & stock projections</small>
          </div>
        </div>
        {[
          {
            icon: Truck,
            count: data.counts.high_delay,
            label: 'elevated delay scores',
            page: 'Transportation',
          },
          {
            icon: Boxes,
            count: data.counts.shortages,
            label: 'projected shortages',
            page: 'Inventory',
          },
          {
            icon: CircleDot,
            count: data.counts.anomalies,
            label: 'unusual shipments',
            page: 'Transportation',
          },
        ].map((x) => (
          <button key={x.label} onClick={() => navigate(x.page as Page)}>
            <x.icon size={18} />
            <strong>{number(x.count)}</strong>
            <span>{x.label}</span>
            <ArrowRight size={14} />
          </button>
        ))}
      </div>
      <div className="two-col">
        <Panel
          title="Delivery performance"
          subtitle="Did shipments arrive by their planned arrival?"
          action={
            <select
              aria-label="Trend period"
              value={period}
              onChange={(e) => setPeriod(+e.target.value)}
            >
              <option value={12}>Last 12 months</option>
              <option value={24}>All history</option>
              <option value={6}>Last 6 months</option>
            </select>
          }
        >
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={data.trend.slice(-period)}
                margin={{ left: -18, right: 15, top: 20 }}
              >
                <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="var(--rule)" />
                <XAxis
                  dataKey="month"
                  tickFormatter={(v) => String(v).slice(2)}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis domain={[0, 100]} unit="%" axisLine={false} tickLine={false} />
                <Tooltip formatter={(v) => [`${number(Number(v), 1)}%`, 'On-time delivery']} />
                <Area
                  isAnimationActive={false}
                  type="monotone"
                  dataKey="on_time"
                  stroke="var(--olive)"
                  strokeWidth={2.5}
                  fill="var(--olive-wash)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-footer">
            <span>
              <i className="legend-dot" />
              Historical on-time delivery
            </span>
            <LinkButton onClick={() => navigate('Transportation')}>Inspect shipments</LinkButton>
          </div>
        </Panel>
        <Panel
          title="Supply network"
          subtitle="Geographic view of European locations and historical flows"
          action={<span className="subtle-tag">{nodes.length} nodes</span>}
        >
          <p className="network-scroll-hint" id="network-scroll-hint">
            Scroll horizontally to explore the network.
          </p>
          <div
            className="network"
            role="region"
            aria-label="Supply network map"
            aria-describedby="network-scroll-hint"
            tabIndex={0}
          >
            <svg
              viewBox="0 0 570 360"
              role="img"
              aria-label="European supply network projected from location coordinates"
            >
              <defs>
                <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 30 0 L 0 0 0 30" fill="none" stroke="var(--rule)" strokeWidth=".7" />
                </pattern>
              </defs>
              <rect width="570" height="360" fill="url(#grid)" />
              <text x="15" y="30" className="map-caption">
                EUROPE / GEOGRAPHIC NETWORK
              </text>
              {data.lanes.map((lane, i) => {
                const a = position(lane.origin_location_id),
                  b = position(lane.destination_location_id)
                return a && b ? (
                  <path
                    key={i}
                    d={`M ${a.x} ${a.y} Q ${(a.x + b.x) / 2 + 35} ${(a.y + b.y) / 2 - 15} ${b.x} ${b.y}`}
                    fill="none"
                    stroke="var(--olive)"
                    strokeWidth={Math.min(2.5, 0.5 + lane.shipments / 700)}
                    opacity=".22"
                  >
                    <title>{lane.shipments} historical shipments</title>
                  </path>
                ) : null
              })}
              {nodes.map((n) => {
                const p = position(n.id)!
                const hub = ['WAREHOUSE', 'PLANT'].includes(n.location_type)
                return (
                  <g key={n.id}>
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r={hub ? 10 : 4}
                      fill={hub ? 'var(--olive-wash)' : 'var(--muted)'}
                      stroke={hub ? 'var(--olive)' : 'white'}
                      strokeWidth={hub ? 2 : 1}
                    >
                      <title>
                        {n.name} · {n.location_type}
                      </title>
                    </circle>
                    {hub && (
                      <text x={p.x + 14} y={p.y - 9} className="map-label">
                        {n.city}
                      </text>
                    )}
                  </g>
                )
              })}
            </svg>
          </div>
          <div className="chart-footer">
            <span>
              <i className="legend-dot" />
              Plants & warehouses
            </span>
            <span>Overseas nodes omitted from this view</span>
          </div>
        </Panel>
      </div>
      <Panel
        className="overview-exceptions"
        title="Prioritized exceptions"
        subtitle="Evidence, business impact and suggested response"
        action={<span className="subtle-tag">{number(data.counts.exceptions)} signals</span>}
      >
        <Exceptions items={exceptions} navigate={navigate} />
      </Panel>
      <Note>
        Historical synthetic data. Delivery and supplier risks replay completed records; inventory
        risks project forward from the balance snapshot. Predictions support review, and should be
        interpreted together with operational context.
      </Note>
    </div>
  )
}
