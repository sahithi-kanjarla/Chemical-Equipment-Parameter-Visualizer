// src/components/TypeChart.jsx
import React from 'react';
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';
import styles from '../styles/TypeChart.module.css';

ChartJS.register(
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

export default function TypeChart({ distribution = {}, summary = null, chartType = 'bar', onChartTypeChange }) {
  const hasDistribution = distribution && Object.keys(distribution).length > 0;
  const labels = hasDistribution ? Object.keys(distribution) : [];
  const counts = hasDistribution ? labels.map((l) => distribution[l]) : [];

  // Distinct color palettes for each chart type
  const barColor = '#007bff';
  const barBorder = '#0056b3';
  const pieColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'];
  const lineColor = '#0056b3';
  const histColor = '#FF6B6B';

  const baseOptions = {
    responsive: true,
    plugins: { legend: { display: chartType !== 'bar' } },
    scales: chartType === 'pie' ? {} : { y: { beginAtZero: true, ticks: { precision: 0 } } },
  };

  const cornerSelect = (
    <div className={styles.chartControls}>
      <select className={styles.controlButton} value={chartType} onChange={(e) => onChartTypeChange && onChartTypeChange(e.target.value)}>
        <option value="bar">Bar</option>
        <option value="pie">Pie</option>
        <option value="line">Line</option>
        <option value="hist">Histogram</option>
      </select>
    </div>
  );

  if (!hasDistribution && chartType !== 'hist') {
    return (
      <div className={styles.chartContainer}>
        {cornerSelect}
        <h5 className={styles.chartTitle}>Type Distribution</h5>
        <div className={styles.chartArea}>
          <div className={styles.emptyState}>No data to display.</div>
        </div>
      </div>
    );
  }

  if (chartType === 'pie') {
    return (
      <div className={styles.chartContainer}>
        {cornerSelect}
        <h5 className={styles.chartTitle}>Type Distribution</h5>
        <div className={styles.chartArea}>
          <div className={styles.labelColumn}>
            {labels.map((label, idx) => (
              <div key={idx} className={styles.labelItem}>
                <div 
                  className={styles.colorDot} 
                  style={{ backgroundColor: pieColors[idx % pieColors.length] }}
                ></div>
                <span className={styles.labelText}>{label}: {counts[idx]}</span>
              </div>
            ))}
          </div>
          <div className={styles.pieCorner}>
            <Pie 
              data={{ 
                labels, 
                datasets: [{ 
                  data: counts,
                  backgroundColor: pieColors,
                  borderColor: '#fff',
                  borderWidth: 2
                }] 
              }} 
              options={{ ...baseOptions, plugins: { ...baseOptions.plugins, legend: { display: false } } }} 
            />
          </div>
        </div>
      </div>
    );
  }
  if (chartType === 'line') {
    return (
      <div className={styles.chartContainer}>
        {cornerSelect}
        <h5 className={styles.chartTitle}>Type Distribution</h5>
        <div className={styles.chartArea}>
          <div className={styles.chartWrapper}>
            <Line 
              data={{ 
                labels, 
                datasets: [{ 
                  data: counts,
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
              options={baseOptions} 
            />
          </div>
        </div>
      </div>
    );
  }
  if (chartType === 'hist') {
    const numericValues = [];
    if (summary && summary.averages) {
      Object.values(summary.averages).forEach(v => {
        if (v != null && !Number.isNaN(v)) numericValues.push(Number(v));
      });
    }
    const values = numericValues.length ? numericValues : counts;
    if (!values || values.length === 0) {
      return (
        <div className={styles.chartContainer}>
          {cornerSelect}
          <h5 className={styles.chartTitle}>Histogram</h5>
          <div className={styles.chartArea}>
            <div className={styles.emptyState}>No numeric data to draw a histogram.</div>
          </div>
        </div>
      );
    }
    // simple bins computed client-side and shown with Bar
    const min = Math.min(...values);
    const max = Math.max(...values);
    const bins = Math.min(10, Math.max(1, Math.ceil(Math.sqrt(values.length))));
    const binSize = (max - min) / bins || 1;
    const histCounts = new Array(bins).fill(0);
    values.forEach((v) => {
      const idx = Math.min(bins - 1, Math.floor((v - min) / binSize));
      histCounts[idx] += 1;
    });
    const histLabels = histCounts.map((_, i) => {
      const a = (min + i * binSize);
      const b = (min + (i + 1) * binSize);
      return `${a.toFixed(1)}–${b.toFixed(1)}`;
    });
    return (
      <div className={styles.chartContainer}>
        {cornerSelect}
        <h5 className={styles.chartTitle}>Histogram</h5>
        <div className={styles.chartArea}>
          <div className={styles.chartWrapper}>
            <Bar 
              data={{ 
                labels: histLabels, 
                datasets: [{ 
                  data: histCounts,
                  backgroundColor: histColor,
                  borderColor: '#C92A2A',
                  borderWidth: 1
                }] 
              }} 
              options={baseOptions} 
            />
          </div>
        </div>
      </div>
    );
  }

  // default bar
  return (
    <div className={styles.chartContainer}>
      {cornerSelect}
      <h5 className={styles.chartTitle}>Type Distribution</h5>
      <div className={styles.chartArea}>
        <div className={styles.chartWrapper}>
          <Bar 
            data={{ 
              labels, 
              datasets: [{ 
                data: counts,
                backgroundColor: barColor,
                borderColor: barBorder,
                borderWidth: 1
              }] 
            }} 
            options={baseOptions} 
          />
        </div>
      </div>
    </div>
  );
}
