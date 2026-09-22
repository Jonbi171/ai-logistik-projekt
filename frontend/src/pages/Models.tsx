import { useMediaQuery } from '../components/responsive'
import { useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ScatterChart,
  Scatter,
} from 'recharts'
import type { ModelCard, Overview } from '../api/tower'
import { TableScroll, Panel, State, Note, Metric } from '../components/ui'
import { useData, number, date } from '../components/data'

const label = (s: string) => s.replaceAll('_', ' ').toUpperCase()
function MetricTable({ metrics }: { metrics: ModelCard['metrics'] }) {
  return (
    <div className="model-metrics">
      {Object.entries(metrics)
        .filter(([, v]) => !Array.isArray(v))
        .map(([k, v]) => (
          <Metric key={k} label={label(k)} value={number(v as number | null, 3)} />
        ))}
    </div>
  )
}
export function Models({ overview }: { overview: Overview }) {
  const result = useData<{ items: ModelCard[] }>('/tower/models')
  const narrow = useMediaQuery('(max-width: 480px)')
  const [selected, setSelected] = useState('delay')
  const card = result.data?.items.find((m) => m.id === selected)
  const weak = card && typeof card.metrics.roc_auc === 'number' && card.metrics.roc_auc < 0.65
  return (
    <>
      <Note>
        Predictions provide decision support and should be interpreted together with operational
        context. Every metric below is calculated from this project’s data; none is a production
        performance claim.
      </Note>
      <State {...result} />
      {result.data && (
        <>
          <div className="model-tabs">
            {result.data.items.map((m) => (
              <button
                key={m.id}
                className={selected === m.id ? 'active' : ''}
                onClick={() => setSelected(m.id)}
              >
                <span>{m.name}</span>
                <small>{m.model}</small>
              </button>
            ))}
          </div>
          {card && (
            <>
              <Panel
                title={card.name}
                subtitle={card.purpose}
                action={<span className="subtle-tag">Experimental · local artifact</span>}
              >
                <div className="detail-panel">
                  {weak && (
                    <Note warning>
                      Limited predictive discrimination: ROC-AUC{' '}
                      {number(card.metrics.roc_auc as number, 3)}. This model is useful for
                      demonstrating the workflow, but needs better explanatory data and calibration
                      before operational use.
                    </Note>
                  )}
                  <MetricTable metrics={card.metrics} />
                  <div className="model-meta">
                    <div>
                      <small>MODEL</small>
                      <strong>{card.model}</strong>
                    </div>
                    <div>
                      <small>DATASET</small>
                      <strong>{number(card.observations)} observations</strong>
                    </div>
                    <div>
                      <small>TRAIN / TEST</small>
                      <strong>
                        {number(card.train_rows)} / {number(card.test_rows)}
                      </strong>
                    </div>
                    <div>
                      <small>TRAINED</small>
                      <strong>{date(card.trained_at)}</strong>
                    </div>
                  </div>
                  <dl className="detail-list">
                    <div>
                      <dt>Target</dt>
                      <dd>{card.target}</dd>
                    </div>
                    <div>
                      <dt>Validation</dt>
                      <dd>{card.validation}</dd>
                    </div>
                    {card.cutoff && (
                      <div>
                        <dt>Holdout begins</dt>
                        <dd>{date(card.cutoff)}</dd>
                      </div>
                    )}
                    <div>
                      <dt>Why this model</dt>
                      <dd>{card.reason}</dd>
                    </div>
                  </dl>
                  <div className="chips">
                    {card.features.map((f) => (
                      <span key={f}>{f}</span>
                    ))}
                  </div>
                </div>
              </Panel>
              <div className="two-col">
                {card.importance.length > 0 && (
                  <Panel
                    title="Global feature importance"
                    subtitle={
                      card.model.includes('Regression')
                        ? 'Absolute coefficients after numeric scaling; association, not causation'
                        : 'Tree impurity importance; association, not causation'
                    }
                  >
                    <div className="chart tall">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={card.importance.map((i) => ({
                            ...i,
                            short:
                              i.feature.length > (narrow ? 17 : 30)
                                ? i.feature.slice(0, narrow ? 14 : 27) + '…'
                                : i.feature,
                          }))}
                          layout="vertical"
                          margin={{ left: 0, right: narrow ? 12 : 30 }}
                        >
                          <XAxis type="number" hide />
                          <YAxis
                            type="category"
                            dataKey="short"
                            width={narrow ? 110 : 185}
                            tick={{ fontSize: 10 }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <Tooltip
                            labelFormatter={(_, payload) => payload[0]?.payload.feature ?? ''}
                          />
                          <Bar
                            isAnimationActive={false}
                            dataKey="importance"
                            fill="var(--olive)"
                            radius={[0, 4, 4, 0]}
                            barSize={13}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </Panel>
                )}
                {card.comparison && (
                  <Panel
                    title="Model comparison"
                    subtitle={`${card.comparison.model} · same holdout and feature set`}
                  >
                    <div className="detail-panel">
                      <MetricTable metrics={card.comparison.metrics} />
                      <Note>
                        The selected demo model is documented above. An alternative can outperform
                        it; a stronger test score alone is not evidence of causal business benefit.
                        Synthetic patterns may make some tasks unusually easy.
                      </Note>
                    </div>
                  </Panel>
                )}
                {Array.isArray(card.metrics.confusion_matrix) && (
                  <Panel
                    title="Confusion matrix"
                    subtitle="Threshold 0.50 · untouched chronological holdout"
                  >
                    <div className="confusion">
                      <span />
                      <span>Predicted on time</span>
                      <span>Predicted late</span>
                      <span>Actual on time</span>
                      <strong>{number(card.metrics.confusion_matrix[0][0])}</strong>
                      <strong>{number(card.metrics.confusion_matrix[0][1])}</strong>
                      <span>Actual late</span>
                      <strong>{number(card.metrics.confusion_matrix[1][0])}</strong>
                      <strong>{number(card.metrics.confusion_matrix[1][1])}</strong>
                    </div>
                  </Panel>
                )}
                {card.samples && card.id !== 'delay' && (
                  <Panel
                    title="Predicted versus observed"
                    subtitle="First 60 chronological holdout predictions"
                  >
                    <div className="chart">
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart
                          margin={{ left: 0, right: narrow ? 8 : 20, top: 20, bottom: 15 }}
                        >
                          <CartesianGrid strokeDasharray="3 5" />
                          <XAxis type="number" dataKey="actual" name="Actual" />
                          <YAxis
                            type="number"
                            dataKey="predicted"
                            name="Predicted"
                            width={narrow ? 45 : 60}
                          />
                          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                          <Scatter
                            isAnimationActive={false}
                            data={card.samples}
                            fill="var(--olive)"
                          />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  </Panel>
                )}
              </div>
            </>
          )}
        </>
      )}
      <Panel
        title="Data provenance & quality"
        subtitle={`${overview.source.source} · extracted ${date(overview.source.extracted_at)}`}
      >
        <TableScroll label="Data quality checks">
          <table>
            <thead>
              <tr>
                <th>Check</th>
                <th>Count</th>
                <th>Interpretation</th>
              </tr>
            </thead>
            <tbody>
              {overview.quality.map((q) => (
                <tr key={q.check}>
                  <td>{q.check}</td>
                  <td>{number(q.value)}</td>
                  <td>{q.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableScroll>
        <div className="detail-panel">
          {overview.limitations.map((l) => (
            <p key={l} className="footnote">
              {l}
            </p>
          ))}
        </div>
      </Panel>
    </>
  )
}
