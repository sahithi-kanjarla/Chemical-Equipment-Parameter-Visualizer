// src/components/ParameterSmallCard.jsx
import React, { useMemo } from 'react';
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
import styles from '../styles/ParameterSmallCard.module.css';

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend, PointElement, LineElement, ArcElement);

const CHOICES = ['bar', 'line', 'pie', 'hist'];

function buildBarData(valuesObj) {
  const labels = Object.keys(valuesObj || {});
  const vals = labels.map(k => {
    const v = valuesObj[k];
    return v === null || v === undefined || Number.isNaN(v) ? null : Number(v);
  });
  return {
    labels,
    datasets: [{ label: 'Value', data: vals }],
  };
}

export default function ParameterSmallCard({ param, values = {}, chartType = 'bar', onChartTypeChange = () => {}, onRemove = () => {} }) {
  const data = useMemo(() => buildBarData(values), [values]);

  const chartOptions = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true } },
  };

  // small top-right control area (chart-type + trash)
  const controlStyle = { position: 'absolute', right: 10, top: 8, zIndex: 5 };

  return (
    <div className={styles.cardContainer}>
      <div className={styles.controlArea}>
        <select className={styles.chartTypeSelect} value={chartType} onChange={(e) => onChartTypeChange(e.target.value)}>
          {CHOICES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <button className={styles.removeButton} title="Remove chart" onClick={onRemove}>🗑️ Remove</button>
      </div>

      <div className={styles.cardHeader}>
        <h6 className={styles.cardTitle}>{param}</h6>
      </div>

      <div className={styles.chartContainer}>
        <div className={styles.chartWrapper}>
          {chartType === 'pie' ? (
            <Pie data={data} />
          ) : chartType === 'line' ? (
            <Line data={data} options={chartOptions} />
          ) : chartType === 'hist' ? (
            // simple histogram built from data values
            (() => {
              const vals = (data.datasets && data.datasets[0].data) || [];
              const numeric = vals.filter(v => typeof v === 'number');
              if (numeric.length === 0) {
                return <div className={styles.errorMessage}>No numeric data</div>;
              }
              // build histogram data for a bar chart
              const min = Math.min(...numeric);
              const max = Math.max(...numeric);
              const bins = Math.min(8, Math.max(1, Math.ceil(Math.sqrt(numeric.length))));
              const binSize = (max - min) / bins || 1;
              const counts = new Array(bins).fill(0);
              numeric.forEach(v => {
                const idx = Math.min(bins - 1, Math.floor((v - min) / binSize));
                counts[idx] += 1;
              });
              const labels = counts.map((_, i) => {
                const a = (min + i * binSize);
                const b = (min + (i + 1) * binSize);
                return `${a.toFixed(1)}–${b.toFixed(1)}`;
              });
              const histData = { labels, datasets: [{ data: counts }] };
              return <Bar data={histData} options={chartOptions} />;
            })()
          ) : (
            <Bar data={data} options={chartOptions} />
          )}
        </div>
      </div>
    </div>
  );
}
