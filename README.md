# Intelligent Control Tower Demo

A locally runnable portfolio demo showing how logistics data becomes **KPIs → predictions → business impact → recommended action**. Built with React, TypeScript, Vite, Recharts, FastAPI, SQLAlchemy, PostgreSQL, pandas and scikit-learn.

## About this branch

`displayed_end_version` illustrates the imagined end product for employers, interviewers and university supervisors. It is separate from the project’s independently developed final implementation. This work does not merge into `develop` or `main`.

## Start

From the repository root:

```bash
./start-demo.sh
```

- Dashboard: **http://127.0.0.1:5173**
- API documentation: **http://127.0.0.1:8000/docs**
- Readiness / data source: **http://127.0.0.1:8000/health**

The script prepares missing dependencies, trains models if artifacts are absent, and starts both servers. Subsequent launches load saved models. **Ctrl+C stops both servers.** The original `./start.sh` also works. Ports 8000 and 5173 must be free.

Prerequisites: Python 3.12+ (verified locally with 3.14), Node.js 22.12+ or 24+, npm, and access to the existing synthetic PostgreSQL database on the first run.

### Database configuration

The existing `backend/database/database.ini` configuration is preserved. Alternatively export `DATABASE_URL` in the shell before starting; PostgreSQL URLs using `postgresql://`, `postgres://`, and `postgresql+psycopg://` are accepted. See [database.ini.example](backend/database/database.ini.example) for the expected keys. Do not commit credentials.

Database extraction uses a **repeatable-read, read-only transaction**. The demo performs no migrations, database resets, inserts or updates. Existing exploration endpoints are preserved and made lazy/read-only.

On startup the backend reads an analytical snapshot from PostgreSQL. It remains consistent for the session; restart to reload operational data. If the database is unreachable, it can use the previously extracted local snapshot, visibly labeled in the dashboard. There is **no generated frontend fallback data**. A fresh checkout needs database access before an offline demo is possible.

```bash
# Prepare dependencies and train missing models without starting servers
./setup-demo.sh

# Explicitly refresh data and retrain models
backend/venv/bin/python -m backend.ml.train_all

# Run entirely from the saved PostgreSQL snapshot
DEMO_OFFLINE=1 ./start-demo.sh

# Retrain from that same snapshot
backend/venv/bin/python -m backend.ml.train_all --offline
```

`DEMO_RETRAIN=1 ./start-demo.sh` forces training during setup. Local snapshots, model artifacts, credentials and virtual environments are gitignored. Do not load joblib files from untrusted sources. Retrain after changes to model code or dependency versions.

## What is implemented

| Workspace | Decision support |
| --- | --- |
| Control Tower | Eight calculated KPIs, delivery trends, geographic network, prioritized exceptions, browser-local review state |
| Transportation | Search and risk/mode filters, held-out delay predictions, ETA, anomalies, linked customer orders, observed outcomes |
| Inventory | Available supply, dated inbound, days of supply, safety stock, shortage timing, excess flags and candidate transfers |
| Demand | 24 SKU forecasts, historical demand, untouched holdout predictions, approximate uncertainty ranges |
| Suppliers | Requested-date OTD, lead time, fill rate, rejection rate and experimental delivery risk |
| Production | Historical capacity utilization, plan attainment, late completions, scrap and downtime |
| AI / ML Insights | Training metadata, features, evaluation metrics, comparisons, confusion matrices and data limitations |
| Scenario Analysis | Interactive freight-cost/service comparison and daily inventory projections with demand/receipt changes |

**Models:** logistic-regression delay baseline, random-forest delay classifier and delay-hours regressor, linear-regression freight model with random-forest comparison, per-SKU last-value/moving-average/exponential-smoothing forecasts, logistic-regression supplier risk, and Isolation Forest anomalies. Inventory projections and recommendations use transparent rules.

**KPIs:** shipment on-time delivery and delay rate, freight spend/cost per km, average transit, forecast WAPE/MAE/RMSE/bias, projected shortages and days of supply, inventory value, supplier performance, capacity utilization, production attainment and scrap. KPI tooltips explain denominators. OTIF and turnover are omitted where required consistent evidence is not established.

## Demo walkthrough

1. Start with **Control Tower** to explain historical performance and projected inventory shortages.
2. Expand an exception and follow **Inspect evidence** to a shipment or inventory position.
3. On a shipment, compare pre-departure predictions with the actual outcome and inspect linked orders.
4. Open **Scenario Analysis** to change shipment attributes and predict freight cost and delivery risk.
5. Select a SKU in **Demand**, then inspect its coverage in **Inventory**.
6. Stress-test inventory: increase demand, add replenishment, and move its arrival beyond the first shortage day.
7. Finish with **AI / ML Insights** to show evaluated performance and model limitations.

## Important limitations

- The supplied dataset is historical and synthetic: all 12,000 shipments are delivered, sales orders are delivered and purchase orders are received. **Shipment and supplier risks are explicitly historical replay**, not live warnings. Inventory balances are dated 29 July 2026.
- Delay and supplier classifiers have weak holdout discrimination. Metrics and confusion matrices expose this; probabilities are uncalibrated. Strong freight-cost performance on synthetic data does not establish real-world generalization.
- Demand uses weekly orders, excludes the last partial week, and tests on the final eight complete weeks. Inventory projections carry the latest forecast level to the later balance date and allocate by recent warehouse demand share. Component/BOM demand is not modeled.
- Confirmed receipts with known future dates are counted once. Undated in-transit inventory and overdue receipts are not assumed to arrive on time. The uncertainty band is an approximate residual range, not a calibrated service guarantee.
- Transfer recommendations are independent candidates, not a jointly optimized allocation plan. Scenarios omit transport capacity, transfer cost and causal effects of carrier changes. Review markers stay in the browser; they do not execute actions or provide a shared audit trail.

The two supplied PDFs inform the design; the explicit demo brief controls scope. See [design and methodology](docs/demo-design.md) for the mapping, formulas and future roadmap.

## Code and verification

- `backend/ml/`: leakage-safe feature builders, training, forecasting and local model artifacts.
- `backend/services/`: database extraction, transport, inventory, supplier/production and overview calculations.
- `backend/app/`: FastAPI routes, validated scenario requests and preserved legacy endpoints.
- `frontend/src/pages/`, `components/`, `api/`: typed React workspaces, shared UI and API client.
- `backend/tests/`, `frontend/tests/`: decision-integrity, API and browser tests.

```bash
backend/venv/bin/python -m unittest discover -s backend/tests -v
npm --prefix frontend run build
npm --prefix frontend run lint
# Browser tests start an offline demo if needed; uses installed Google Chrome
cd frontend
npx playwright test
```

Backend integration tests require the prepared local snapshot/models; pure calculation tests do not. To check startup and shutdown directly (with ports free), run `backend/venv/bin/python backend/tests/check_startup.py`. It verifies PostgreSQL and offline startup, cached artifacts and Ctrl+C cleanup.

Browser verification covers all eight pages, shipment filtering and drilldown, both scenarios, demand selection, model comparison, persisted review state, mobile layout and retry after API failure.
