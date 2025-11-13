// src/components/ParameterAnalysisChart.jsx
import React, { useMemo, useState } from 'react';
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const PARAMETERS = ['Flowrate', 'Pressure', 'Temperature'];

function buildChartData(perTypeObj, param) {
  const labels = Object.keys(perTypeObj || {});
  const values = labels.map((k) => {
    const v = perTypeObj[k];
    return v === null || v === undefined || Number.isNaN(v) ? null : Number(v);
  });
  return {
    labels,
    datasets: [{ label: `Average ${param}`, data: values }],
  };
}

export default function ParameterAnalysisChart({ summary = {} }) {
  const [mode, setMode] = useState('single'); // 'single' or 'multi'
  const [param, setParam] = useState('Flowrate');

  // per_type_averages shape: { Flowrate: {Type: val}, Pressure: {...}, Temperature: {...} }
  const perTypeAverages = summary.per_type_averages || {};

  // convenience: for single mode
  const perTypeForParam = perTypeAverages[param] || {};

  const hasAnyData = PARAMETERS.some((p) => {
    const obj = perTypeAverages[p];
    return obj && Object.keys(obj).length > 0;
  });

  const chartOptions = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true } },
  };

  // memoize chart data
  const singleData = useMemo(() => buildChartData(perTypeForParam, param), [perTypeForParam, param]);

  return (
    <div className="card p-3 mb-3">
      <div className="d-flex justify-content-between align-items-center mb-2">
        <h5 className="mb-0">Parameter Analysis</h5>
        <div className="d-flex align-items-center gap-2">
          <div className="btn-group btn-group-sm" role="group">
            <button
              type="button"
              className={`btn btn-outline-primary ${mode === 'single' ? 'active' : ''}`}
              onClick={() => setMode('single')}
            >
              Single
            </button>
            <button
              type="button"
              className={`btn btn-outline-primary ${mode === 'multi' ? 'active' : ''}`}
              onClick={() => setMode('multi')}
            >
              Multi
            </button>
          </div>

          {mode === 'single' && (
            <div className="d-flex align-items-center ms-2">
              <label className="me-2 mb-0">Analyze:</label>
              <select
                className="form-select form-select-sm"
                value={param}
                onChange={(e) => setParam(e.target.value)}
              >
                {PARAMETERS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          )}
        </div>
      </div>

      {!hasAnyData ? (
        <div className="text-muted">No per-type averages available. Upload a dataset to compute per-type averages.</div>
      ) : (
        <>
          {mode === 'single' ? (
            <div>
              <h6 className="mb-2">Average {param} by Type</h6>
              <Bar data={singleData} options={chartOptions} />
              <div className="mt-2 text-muted small">
                This chart shows the average <strong>{param}</strong> for each equipment type (computed at upload).
              </div>
            </div>
          ) : (
            // Multi mode: show small multiples for each parameter
            <div className="row">
              {PARAMETERS.map((p) => {
                const obj = perTypeAverages[p] || {};
                const labels = Object.keys(obj);
                const has = labels.length > 0;
                const data = buildChartData(obj, p);
                return (
                  <div className="col-12 col-md-6 mb-3" key={p}>
                    <div className="border rounded p-2 h-100">
                      <h6 className="mb-2">Average {p} by Type</h6>
                      {has ? (
                        <Bar data={data} options={chartOptions} />
                      ) : (
                        <div className="text-muted">No data for {p}.</div>
                      )}
                      <div className="mt-2 text-muted small">
                        Average <strong>{p}</strong> per equipment type.
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
