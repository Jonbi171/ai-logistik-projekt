import { lazy, Suspense, useCallback, useState } from 'react'
import {
  Activity,
  ArrowUpRight,
  Boxes,
  BrainCircuit,
  ChevronRight,
  Database,
  Factory,
  FlaskConical,
  LayoutDashboard,
  Menu,
  Package,
  Truck,
  Users,
  X,
} from 'lucide-react'
import type { Overview as OverviewData, Exception, Page } from '../api/tower'
import { State } from '../components/ui'
import { useMediaQuery, useModal } from '../components/responsive'
import { useData, date } from '../components/data'
const Overview = lazy(() => import('../pages/Overview').then((m) => ({ default: m.Overview })))
const Transportation = lazy(() =>
  import('../pages/Transportation').then((m) => ({ default: m.Transportation })),
)
const Inventory = lazy(() => import('../pages/Inventory').then((m) => ({ default: m.Inventory })))
const Demand = lazy(() => import('../pages/Demand').then((m) => ({ default: m.Demand })))
const Production = lazy(() => import('../pages/Supply').then((m) => ({ default: m.Production })))
const Suppliers = lazy(() => import('../pages/Supply').then((m) => ({ default: m.Suppliers })))
const Models = lazy(() => import('../pages/Models').then((m) => ({ default: m.Models })))
const Scenarios = lazy(() => import('../pages/Scenarios').then((m) => ({ default: m.Scenarios })))
import './App.css'
import './mobile.css'

const pages: { name: Page; icon: typeof Activity; group: string; description: string }[] = [
  {
    name: 'Control Tower',
    icon: LayoutDashboard,
    group: 'WORKSPACE',
    description: 'Delivery history, inventory coverage and exceptions to review.',
  },
  {
    name: 'Transportation',
    icon: Truck,
    group: '',
    description: 'Review shipments, delivery estimates and freight costs.',
  },
  {
    name: 'Inventory',
    icon: Boxes,
    group: '',
    description: 'Connect inventory coverage to forecast demand and incoming supply.',
  },
  {
    name: 'Demand',
    icon: Activity,
    group: '',
    description: 'Compare demand history, forecasts and holdout results.',
  },
  {
    name: 'Suppliers',
    icon: Users,
    group: '',
    description: 'Compare supplier reliability, lead times, and quality.',
  },
  {
    name: 'Production',
    icon: Factory,
    group: '',
    description: 'Understand output, capacity utilization, and production performance.',
  },
  {
    name: 'AI / ML Insights',
    icon: BrainCircuit,
    group: 'INTELLIGENCE',
    description: 'Inspect training data, evaluation results and model limitations.',
  },
  {
    name: 'Scenario Analysis',
    icon: FlaskConical,
    group: '',
    description: 'Compare changes to freight cost, delivery risk and stock coverage.',
  },
]
function pageLabel(page: Page): string {
  return page
    .replace('Control Tower', 'Control tower')
    .replace('AI / ML Insights', 'AI / ML insights')
    .replace('Scenario Analysis', 'Scenario analysis')
}
function initialPage(): Page {
  const requested = decodeURIComponent(window.location.hash.slice(1))
  return pages.some((p) => p.name === requested) ? (requested as Page) : 'Control Tower'
}
function App() {
  const [page, setPage] = useState<Page>(initialPage),
    [reference, setReference] = useState<string | undefined>(),
    [menu, setMenu] = useState(false)
  const overview = useData<OverviewData>('/tower/overview'),
    exceptions = useData<{ items: Exception[] }>('/tower/exceptions')
  const config = pages.find((p) => p.name === page)!
  const navigate = useCallback((p: Page, ref?: string) => {
    setPage(p)
    setReference(ref)
    setMenu(false)
    window.history.replaceState(null, '', `#${encodeURIComponent(p)}`)
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [])
  const mobile = useMediaQuery('(max-width: 760px)')
  const mobileMenu = mobile && menu
  const closeMenu = useCallback(() => setMenu(false), [])
  const menuRef = useModal(mobileMenu, closeMenu)
  return (
    <div className="app-shell">
      <aside
        ref={menuRef}
        id="workspace-navigation"
        className={`sidebar ${mobileMenu ? 'open' : ''}`}
        inert={mobile && !mobileMenu}
        role={mobileMenu ? 'dialog' : undefined}
        aria-modal={mobileMenu ? true : undefined}
        aria-label={mobileMenu ? 'Workspace navigation' : undefined}
      >
        <a
          href="#Control%20Tower"
          className="brand"
          onClick={(e) => {
            e.preventDefault()
            navigate('Control Tower')
          }}
        >
          <span className="brand-symbol">B</span>
          <div>
            BillgerICT<span>Intelligent control tower</span>
          </div>
        </a>
        <button
          className="mobile-close icon-button"
          aria-label="Close menu"
          data-modal-close
          onClick={() => setMenu(false)}
        >
          <X />
        </button>
        <div className="workspace-label">
          <span>Operations desk</span>
          <small>Supply chain / Europe</small>
        </div>
        <nav aria-label="Main navigation">
          {pages.map((p) => (
            <div key={p.name}>
              {p.group && <p className="nav-group">{p.group}</p>}
              <button
                className={page === p.name ? 'active' : ''}
                aria-current={page === p.name ? 'page' : undefined}
                onClick={() => navigate(p.name)}
              >
                <p.icon size={18} />
                <span>{pageLabel(p.name)}</span>
                {p.name === 'Control Tower' && <span className="nav-dot" />}
              </button>
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="demo-tag">
            <span />
            Historical synthetic data
          </div>
          <p>
            Shipment history & stock projections.
            <br />
            For analysis and planning.
          </p>
          <a
            href={import.meta.env.DEV ? 'http://127.0.0.1:8000/docs' : '/api-docs'}
            target="_blank"
            rel="noreferrer"
          >
            Explore the API <ArrowUpRight size={14} />
          </a>
        </div>
      </aside>
      {mobileMenu && (
        <button
          className="mobile-shade"
          aria-label="Close navigation"
          onClick={() => setMenu(false)}
        />
      )}
      <div className="main-shell" inert={mobileMenu}>
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="mobile-toggle icon-button"
              aria-label="Open navigation"
              aria-expanded={mobileMenu}
              aria-controls="workspace-navigation"
              onClick={() => setMenu(true)}
            >
              <Menu size={20} />
            </button>
            <Package size={16} />
            <span>Supply chain</span>
            <ChevronRight size={13} />
            <strong>{pageLabel(page)}</strong>
          </div>
          <div className="topbar-right">
            <span className="edition-label">Operations / BillgerICT</span>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <span className="eyebrow">
                BILLGERICT /{' '}
                {page === 'Control Tower' ? 'EXECUTIVE OVERVIEW' : 'DECISION WORKSPACE'}
              </span>
              <h1>{pageLabel(page)}</h1>
              <p>{config.description}</p>
            </div>
            {overview.data && (
              <div className="snapshot-label">
                <Database size={16} />
                <div>
                  <strong>
                    {overview.data.source.offline
                      ? 'Saved PostgreSQL snapshot'
                      : 'PostgreSQL analytical snapshot'}
                  </strong>
                  <span>Inventory as of {date(overview.data.as_of)}</span>
                </div>
              </div>
            )}
          </div>
          <State {...overview} />
          {overview.data && (
            <Suspense fallback={<State loading error={null} />}>
              <>
                {page === 'Control Tower' && (
                  <>
                    {exceptions.error ? (
                      <State {...exceptions} />
                    ) : (
                      <Overview
                        data={overview.data}
                        exceptions={exceptions.data?.items ?? []}
                        navigate={navigate}
                      />
                    )}
                  </>
                )}
                {page === 'Transportation' && (
                  <Transportation
                    key={`${page}-${reference}`}
                    reference={reference}
                    navigate={navigate}
                  />
                )}
                {page === 'Inventory' && (
                  <Inventory
                    key={`${page}-${reference}`}
                    reference={reference}
                    navigate={navigate}
                  />
                )}
                {page === 'Demand' && (
                  <Demand key={`${page}-${reference}`} reference={reference} navigate={navigate} />
                )}
                {page === 'Suppliers' && <Suppliers />}
                {page === 'Production' && <Production />}
                {page === 'AI / ML Insights' && <Models overview={overview.data} />}
                {page === 'Scenario Analysis' && (
                  <Scenarios key={`${page}-${reference}`} reference={reference} />
                )}
              </>
            </Suspense>
          )}
          <footer className="page-footer">
            <span>BillgerICT · Intelligent control tower</span>
            <span>Supply chain analysis</span>
          </footer>
        </main>
      </div>
    </div>
  )
}
export default App
