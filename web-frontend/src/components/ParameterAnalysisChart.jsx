// src/components/ParameterAnalysisChart.jsx
import React from 'react';
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
  ArcElement,
} from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';
import styles from '../styles/ParameterAnalysisChart.module.css';

ChartJS.register(
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
  ArcElement
);

const PARAMETERS = ['Flowrate', 'Pressure', 'Temperature'];

/**
 * SmallChart renders a chart of the requested type inside a .chartWrapper
 * - maintainAspectRatio: false so CSS-controlled heights work for all types
 * - redraw + chartKey to force a safe re-render when props change
 */
function SmallChart({ type, labels, data }) {
  const baseOpts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: type === 'pie' },
      tooltip: { mode: 'index', intersect: false },
    },
    interaction: { mode: 'nearest', intersect: false },
    elements: { point: { radius: 3 } },
    scales: type === 'pie' ? {} : { y: { beginAtZero: true } },
  };

  const chartKey = `${type}-${labels.length}-${labels.join('|')}`;

  const colors = {
    barBg: '#007bff',
    barBorder: '#0056b3',
    line: '#0056b3',
    pie: [
      '#FF6B6B',
      '#4ECDC4',
      '#45B7D1',
      '#FFA07A',
      '#98D8C8',
      '#F7DC6F',
      '#BB8FCE',
      '#85C1E2',
    ],
  };

  const ChartWrapper = ({ children }) => (
    <div className={styles.chartWrapper} key={chartKey}>
      {children}
    </div>
  );

  if (type === 'bar') {
    return (
      <ChartWrapper>
        <Bar
          data={{
            labels,
            datasets: [
              {
                data,
                backgroundColor: colors.barBg,
                borderColor: colors.barBorder,
                borderWidth: 1,
                borderRadius: 6
              },
            ],
          }}
          options={baseOpts}
          redraw
        />
      </ChartWrapper>
    );
  }

  if (type === 'line') {
    return (
      <ChartWrapper>
        <Line
          data={{
            labels,
            datasets: [
              {
                data,
                borderColor: colors.line,
                backgroundColor: 'rgba(0,86,179,0.08)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
              },
            ],
          }}
          options={baseOpts}
          redraw
        />
      </ChartWrapper>
    );
  }

  if (type === 'pie') {
    return (
      <ChartWrapper>
        <Pie
          data={{
            labels,
            datasets: [
              {
                data,
                backgroundColor: colors.pie,
                borderColor: '#fff',
                borderWidth: 1,
              },
            ],
          }}
          options={baseOpts}
          redraw
        />
      </ChartWrapper>
    );
  }

  if (type === 'hist') {
    const vals = Array.isArray(data) ? data : [];
    if (vals.length === 0) return <div className="text-muted small">No numeric data for histogram.</div>;

    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const bins = Math.min(10, Math.ceil(Math.sqrt(vals.length)));
    const binSize = (max - min) / bins || 1;

    const counts = new Array(bins).fill(0);
    vals.forEach((v) => {
      const idx = Math.min(bins - 1, Math.floor((v - min) / binSize));
      counts[idx] += 1;
    });

    const histLabels = counts.map((_, i) => `${(min + i * binSize).toFixed(1)}–${(min + (i + 1) * binSize).toFixed(1)}`);

    return (
      <ChartWrapper>
        <Bar
          data={{
            labels: histLabels,
            datasets: [
              {
                data: counts,
                backgroundColor: '#FF6B6B',
                borderColor: '#C92A2A',
                borderWidth: 1,
              },
            ],
          }}
          options={baseOpts}
          redraw
        />
      </ChartWrapper>
    );
  }

  return null;
}

/**
 * ParameterAnalysisChart - main exported component
 */
export default function ParameterAnalysisChart({
  summary = {},
  analysisChartTypes = {},
  onChangeChartType = () => {},
  onRemoveChart = () => {},
  removedCharts = [],
  onRestoreChart = () => {},
}) {
  const perType = (summary && summary.per_type_averages) || {};
  const removedSet = Array.isArray(removedCharts) ? new Set(removedCharts) : new Set(removedCharts);

  return (
    <div className={styles.chartContainer}>
      <h5 className={styles.chartTitle}>Parameter Analysis</h5>

      <div className={styles.gridWrapper || ''}>
        {PARAMETERS.map((param) => {
          const removed = removedSet.has(param);

          if (removed) {
            return (
              <div key={param} className={styles.removedCard || styles.parameterCard}>
                <div><strong>{param}</strong> — removed</div>
                <button className={styles.restoreButton || styles.controlButton} onClick={() => onRestoreChart(param)}>
                  Restore
                </button>
              </div>
            );
          }

          const valuesObj = perType[param] || {};
          const labels = Object.keys(valuesObj);
          const values = labels.map((k) => {
            const v = valuesObj[k];
            return v == null || Number.isNaN(Number(v)) ? 0 : Number(v);
          });

          const chartType = (analysisChartTypes && analysisChartTypes[param]) || 'bar';

          return (
            <div key={param} className={styles.parameterCard}>
              <div className={styles.parameterControls}>
                <select
                  className={styles.controlButton}
                  value={chartType}
                  onChange={(e) => onChangeChartType(param, e.target.value)}
                  aria-label={`Chart type for ${param}`}
                >
                  <option value="bar">Bar</option>
                  <option value="pie">Pie</option>
                  <option value="line">Line</option>
                  <option value="hist">Histogram</option>
                </select>

                <button
                  className={styles.removeButton}
                  title="Remove chart"
                  onClick={() => onRemoveChart(param)}
                  aria-label={`Remove ${param} chart`}
                >
                  {/* simple X icon */}
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>

              <h6 className={styles.parameterTitle}>{param}</h6>

              <div className={styles.parameterChartArea}>
                {labels.length === 0 ? (
                  <div className={styles.emptyState}>No data for {param}.</div>
                ) : (
                  <SmallChart type={chartType} labels={labels} data={values} />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
