// src/components/TypeChart.jsx
import React, { useMemo, useRef, useEffect, useState } from 'react';
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

export default function TypeChart({
  distribution = {},
  summary = null,
  chartType = 'bar',
  onChartTypeChange = () => {},
  // optional external overrides
  externalOptions = {},
}) {
  const containerRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(800);
  const [innerType, setInnerType] = useState(chartType);

  useEffect(() => setInnerType(chartType), [chartType]);

  // ResizeObserver to measure available width (used to tune tick truncation/rotation)
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = Math.round(entry.contentRect.width || entry.target.clientWidth || 800);
        setContainerWidth(w);
      }
    });
    ro.observe(el);
    setContainerWidth(el.clientWidth || 800);
    return () => ro.disconnect();
  }, []);

  const hasDistribution = distribution && Object.keys(distribution).length > 0;
  const labels = hasDistribution ? Object.keys(distribution) : [];
  const counts = hasDistribution ? labels.map((l) => Number(distribution[l] || 0)) : [];

  // helper to truncate strings based on container width
  const truncate = (s, maxLen) => {
    if (typeof s !== 'string') return s;
    if (s.length <= maxLen) return s;
    return s.slice(0, Math.max(3, maxLen - 1)).trim() + '…';
  };

  // Build base options tuned for responsiveness and label handling
  const baseOptions = useMemo(() => {
    const narrow = containerWidth < 420;
    const mid = containerWidth >= 420 && containerWidth < 800;
    const maxRotation = narrow ? 35 : mid ? 20 : 0;
    const tickLimit = narrow ? 6 : mid ? 10 : 14; // length limit for tick label truncation

    return {
      responsive: true,
      maintainAspectRatio: false, // let wrapper height control it
      layout: { padding: { top: 6, right: 6, bottom: 8, left: 6 } },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => {
              const idx = items && items[0] && items[0].dataIndex;
              return (labels[idx] ?? '') + (typeof labels[idx] === 'string' && labels[idx].length > 60 ? '\n(hover for full)' : '');
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            autoSkip: true,
            maxRotation,
            minRotation: 0,
            callback: function (value, index) {
              // Chart.js v3 uses index to get label
              const label = this.getLabelForValue ? this.getLabelForValue(value) : labels[index] ?? '';
              return truncate(label, tickLimit);
            },
            padding: 6,
          },
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          ticks: { precision: 0 },
        },
      },
      elements: {
        bar: {
          borderRadius: 6,
          borderSkipped: false,
          barPercentage: 0.68,
          categoryPercentage: 0.62,
        },
        point: { radius: 3 },
      },
      interaction: { mode: 'index', axis: 'x', intersect: false },
    };
  }, [containerWidth, labels]);

  // merge external options but preserve maintainAspectRatio:false
  const mergedOptions = useMemo(() => ({ ...baseOptions, ...externalOptions, maintainAspectRatio: false }), [baseOptions, externalOptions]);

  const chartData = useMemo(() => ({
    labels,
    datasets: [{
      label: 'Count',
      data: counts,
      backgroundColor: '#007bff',
      borderColor: '#0056b3',
      borderWidth: 1,
    }],
  }), [labels, counts]);

  // Controls UI (corner). Keep simple and accessible.
  const cornerSelect = (
    <div className={styles.chartControls}>
      <select
        className={styles.controlButton}
        value={innerType}
        onChange={(e) => {
          const v = e.target.value;
          setInnerType(v);
          onChartTypeChange && onChartTypeChange(v);
        }}
        aria-label="Change chart type"
      >
        <option value="bar">Bar</option>
        <option value="pie">Pie</option>
        <option value="line">Line</option>
        <option value="hist">Histogram</option>
      </select>
    </div>
  );

  // Small no-data fallback
  if (!hasDistribution && innerType !== 'hist') {
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

  const ChartComponent = innerType === 'pie' ? Pie : innerType === 'line' ? Line : Bar;

  // Pie layout: show small legend/labels and pie on right
  if (innerType === 'pie') {
    const pieColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'];
    const pieData = {
      labels,
      datasets: [{
        data: counts,
        backgroundColor: pieColors,
        borderColor: '#fff',
        borderWidth: 1,
      }],
    };

    return (
      <div className={styles.chartContainer}>
        {cornerSelect}
        <h5 className={styles.chartTitle}>Type Distribution</h5>
        <div className={styles.chartArea}>
          <div className={styles.labelColumn}>
            {labels.map((label, idx) => (
              <div key={idx} className={styles.labelItem}>
                <div className={styles.colorDot} style={{ backgroundColor: pieColors[idx % pieColors.length] }} />
                <span className={styles.labelText}>{label}: {counts[idx]}</span>
              </div>
            ))}
          </div>

          <div ref={containerRef} className={styles.pieCorner}>
            <div className={styles.chartWrapper}>
              <Pie data={pieData} options={{ ...mergedOptions, plugins: { ...mergedOptions.plugins, legend: { display: false } } }} redraw />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Histogram (simple numeric histogram using summary averages or counts)
  if (innerType === 'hist') {
    const numericVals = [];
    if (summary && summary.averages) {
      Object.values(summary.averages).forEach((v) => {
        if (v != null && !Number.isNaN(Number(v))) numericVals.push(Number(v));
      });
    }
    const values = numericVals.length ? numericVals : counts.slice();
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

    const min = Math.min(...values);
    const max = Math.max(...values);
    const bins = Math.min(10, Math.max(1, Math.ceil(Math.sqrt(values.length))));
    const binSize = (max - min) / bins || 1;
    const histCounts = new Array(bins).fill(0);
    values.forEach((v) => {
      const idx = Math.min(bins - 1, Math.floor((v - min) / binSize));
      histCounts[idx] += 1;
    });
    const histLabels = histCounts.map((_, i) => `${(min + i * binSize).toFixed(1)}–${(min + (i + 1) * binSize).toFixed(1)}`);

    return (
      <div className={styles.chartContainer}>
        {cornerSelect}
        <h5 className={styles.chartTitle}>Histogram</h5>
        <div className={styles.chartArea}>
          <div ref={containerRef} className={styles.chartWrapper}>
            <Bar
              data={{ labels: histLabels, datasets: [{ data: histCounts, backgroundColor: '#FF6B6B', borderColor: '#C92A2A', borderWidth: 1 }] }}
              options={mergedOptions}
              redraw
            />
          </div>
        </div>
      </div>
    );
  }

  // default: bar or line
  return (
    <div className={styles.chartContainer}>
      {cornerSelect}
      <h5 className={styles.chartTitle}>Type Distribution</h5>
      <div className={styles.chartArea}>
        <div ref={containerRef} className={styles.chartWrapper}>
          <ChartComponent data={chartData} options={mergedOptions} redraw />
        </div>
      </div>
    </div>
  );
}
