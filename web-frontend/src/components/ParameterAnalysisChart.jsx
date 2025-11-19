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

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend, PointElement, LineElement, ArcElement);

const PARAMETERS = ['Flowrate', 'Pressure', 'Temperature'];

function SmallChart({ type, labels, data }) {
  const baseOpts = { responsive: true, maintainAspectRatio: true };
  
  // Distinct color palettes for each chart type
  const barColor = '#007bff';
  const barBorder = '#0056b3';
  const pieColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'];
  const lineColor = '#0056b3';
  const histColor = '#FF6B6B';
  
  const opts = {
    ...baseOpts,
    plugins: { legend: { display: type === 'pie' } },
    scales: type === 'pie' ? {} : { y: { beginAtZero: true } }
  };

  if (type === 'bar') {
    return (
      <Bar 
        data={{ 
          labels, 
          datasets: [{ 
            data,
            backgroundColor: barColor,
            borderColor: barBorder,
            borderWidth: 1
          }] 
        }} 
        options={opts} 
      />
    );
  }
  if (type === 'line') {
    return (
      <Line 
        data={{ 
          labels, 
          datasets: [{ 
            data,
            borderColor: lineColor,
            backgroundColor: 'rgba(0, 86, 179, 0.1)',
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: lineColor,
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 5
          }] 
        }} 
        options={opts} 
      />
    );
  }
  if (type === 'pie') {
    return (
      <div style={{ width: '100%', height: '280px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Pie data={{ labels, datasets: [{ data, backgroundColor: pieColors, borderColor: '#fff', borderWidth: 2 }] }} options={opts} />
      </div>
    );
  }
  if (type === 'hist') {
    const vals = Array.isArray(data) ? data : [];
    if (vals.length === 0) return <div className="text-muted small">No numeric data for histogram.</div>;
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const bins = Math.min(10, Math.max(1, Math.ceil(Math.sqrt(vals.length || 1))));
    const binSize = (max - min) / bins || 1;
    const histCounts = new Array(bins).fill(0);
    vals.forEach((v) => {
      const idx = Math.min(bins - 1, Math.floor((v - min) / binSize));
      histCounts[idx] += 1;
    });
    const histLabels = histCounts.map((_, i) => {
      const a = (min + i * binSize);
      const b = (min + (i + 1) * binSize);
      return `${a.toFixed(1)}–${b.toFixed(1)}`;
    });
    return (
      <Bar 
        data={{ 
          labels: histLabels, 
          datasets: [{ 
            data: histCounts,
            backgroundColor: '#FF6B6B',
            borderColor: '#C92A2A',
            borderWidth: 1
          }] 
        }} 
        options={opts} 
      />
    );
  }
  return (
    <Bar 
      data={{ 
        labels, 
        datasets: [{ 
          data,
          backgroundColor: '#007bff',
          borderColor: '#0056b3',
          borderWidth: 1
        }] 
      }} 
      options={opts} 
    />
  );
}

function TrashIcon({ width = 14, height = 14 }) {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <line x1="10" y1="11" x2="10" y2="17" />
      <line x1="14" y1="11" x2="14" y2="17" />
    </svg>
  );
}

export default function ParameterAnalysisChart({
  summary = {},
  analysisChartTypes = {},
  onChangeChartType = () => {},
  onRemoveChart = () => {},
  removedCharts = [],
  onRestoreChart = () => {},
}) {
  const perType = (summary && summary.per_type_averages) || {};

  // normalize removedCharts to a Set or array
  const removedSet = Array.isArray(removedCharts) ? new Set(removedCharts) : (removedCharts instanceof Set ? removedCharts : new Set());

  return (
    <div className={styles.chartContainer}>
      <h5 className={styles.chartTitle}>Parameter Analysis</h5>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
        {PARAMETERS.map((param) => {
          const removed = removedSet.has(param);
          if (removed) {
            return (
              <div key={param} style={{ backgroundColor: '#f5f5f5', borderRadius: '8px', padding: '16px', border: '2px dashed #ccc', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div><strong>{param}</strong> — removed</div>
                <button className={styles.controlButton} onClick={() => onRestoreChart(param)}>Restore</button>
              </div>
            );
          }

          const valuesObj = perType[param] || {};
          const labels = Object.keys(valuesObj);
          // values array (for histogram fallback) and chart data for chartjs
          const values = labels.map((k) => (valuesObj[k] == null ? 0 : Number(valuesObj[k])));

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
                  <TrashIcon width={14} height={14} />
                </button>
              </div>

              <h6 className={styles.parameterTitle}>{param}</h6>
              <div className={styles.parameterChartArea}>
                {labels.length === 0 ? (
                  <div style={{ color: '#999', fontSize: '14px' }}>No data for {param}.</div>
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
