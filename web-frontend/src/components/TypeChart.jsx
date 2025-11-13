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

/**
 * TypeChart
 * Props:
 * - distribution: { typeName: count, ... }   // required for type-count charts
 * - summary: full summary object (may contain averages as summary.averages)
 * - chartType: 'bar' | 'pie' | 'line' | 'hist' | 'avg'
 */
export default function TypeChart({ distribution = {}, summary = null, chartType = 'bar' }) {
  // friendly empty state
  const hasDistribution = distribution && Object.keys(distribution).length > 0;
  if (!hasDistribution && chartType !== 'avg' && chartType !== 'hist') {
    return (
      <div className="card p-3 mb-3">
        <h5>Type Distribution</h5>
        <p className="text-muted">No data to display.</p>
      </div>
    );
  }

  // labels and counts for type-based charts
  const labels = hasDistribution ? Object.keys(distribution) : [];
  const counts = hasDistribution ? labels.map((l) => distribution[l]) : [];

  const baseOptions = {
    responsive: true,
    plugins: { legend: { display: chartType !== 'bar' } },
    scales: chartType === 'pie' ? {} : { y: { beginAtZero: true, ticks: { precision: 0 } } },
  };

  // HISTOGRAM: uses numeric averages from summary.averages fallback to counts
  if (chartType === 'hist') {
    const numericValues = [];
    if (summary && summary.averages) {
      Object.values(summary.averages).forEach((v) => {
        if (v != null && !Number.isNaN(v)) numericValues.push(Number(v));
      });
    }
    // fallback to counts (if no numeric values)
    const values = numericValues.length ? numericValues : counts;
    if (!values || values.length === 0) {
      return (
        <div className="card p-3 mb-3">
          <h5>Histogram</h5>
          <p className="text-muted">No numeric data to draw a histogram.</p>
        </div>
      );
    }
    // simple histogram bins
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
    const histData = { labels: histLabels, datasets: [{ label: 'Frequency', data: histCounts }] };

    return (
      <div className="card p-3 mb-3">
        <h5>Histogram</h5>
        <Bar data={histData} options={baseOptions} />
      </div>
    );
  }

  // AVERAGE PER TYPE (Flowrate)
  if (chartType === 'avg') {
    // We expect the backend to provide per-type aggregation ideally.
    // But here we derive per-type average from the summary if possible:
    // summary might not have per-type averages; if not, show helpful message.
    // If your backend provides a `per_type_averages` field in the future, use that.
    // For now, we try a fallback: if `summary._by_type_averages` or similar exists, prefer it.
    let perTypeAverages = null;

    // try different possible summary shapes for per-type averages
    if (summary && summary.per_type_averages && typeof summary.per_type_averages === 'object') {
      perTypeAverages = summary.per_type_averages;
    }

    // fallback: if distribution exists and summary.averages exists,
    // we cannot compute per-type averages accurately without row-level data.
    // So instruct the user to use histogram or upload dataset to compute server-side.
    if (!perTypeAverages) {
      // We can't compute per-type averages reliably here — ask server or compute on upload.
      return (
        <div className="card p-3 mb-3">
          <h5>Per-type average (Flowrate)</h5>
          <p className="text-muted">
            Per-type averages are not available. To enable this, the backend must compute per-type
            averages on upload (recommended). For now, try the histogram or type distribution.
          </p>
        </div>
      );
    }

    const ptLabels = Object.keys(perTypeAverages);
    const ptValues = ptLabels.map((k) => perTypeAverages[k]);

    const data = {
      labels: ptLabels,
      datasets: [{ label: 'Average Flowrate', data: ptValues }],
    };

    return (
      <div className="card p-3 mb-3">
        <h5>Average Flowrate by Type</h5>
        <Bar data={data} options={baseOptions} />
      </div>
    );
  }

  // PIE / LINE / BAR for type counts
  const data = {
    labels,
    datasets: [{ label: 'Count by Equipment Type', data: counts }],
  };

  if (chartType === 'pie') {
    return (
      <div className="card p-3 mb-3">
        <h5>Type Distribution</h5>
        <Pie data={data} options={baseOptions} />
      </div>
    );
  }

  if (chartType === 'line') {
    return (
      <div className="card p-3 mb-3">
        <h5>Type Distribution (line)</h5>
        <Line data={data} options={baseOptions} />
      </div>
    );
  }

  // default: bar
  return (
    <div className="card p-3 mb-3">
      <h5>Type Distribution</h5>
      <Bar data={data} options={baseOptions} />
    </div>
  );
}
