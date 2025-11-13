// src/components/PDFModal.jsx
import React, { useState } from 'react';
import api from '../api';

const CHART_TYPES = [
  { value: 'bar', label: 'Bar' },
  { value: 'pie', label: 'Pie' },
  { value: 'line', label: 'Line' },
  { value: 'hist', label: 'Histogram' },
];

export default function PDFModal({ show, onClose, summary, previewRows, defaultFilename = 'report.pdf' }) {
  const [includeSummary, setIncludeSummary] = useState(true);
  const [includeTypeChart, setIncludeTypeChart] = useState(true);
  const [typeChartType, setTypeChartType] = useState('bar');

  const [includeAnalysis, setIncludeAnalysis] = useState(false);
  const [analysisMode, setAnalysisMode] = useState('single'); // single | multi
  const [analysisParam, setAnalysisParam] = useState('Flowrate');
  const [analysisChartType, setAnalysisChartType] = useState('bar');

  const [includePreview, setIncludePreview] = useState(true);
  const [filename, setFilename] = useState(defaultFilename);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const payload = {
        filename,
        include: {
          summary: includeSummary,
          type_chart: includeTypeChart,
          type_chart_type: typeChartType,
          analysis: {
            include: includeAnalysis,
            mode: analysisMode,
            parameter: analysisParam,
            chart_type: analysisChartType,
          },
          preview_rows: includePreview,
        },
        summary: summary || {},
        preview_rows: includePreview ? previewRows || [] : [],
      };

      const res = await api.post('report-from-summary/', payload, { responseType: 'blob' });
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'report.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      onClose && onClose();
    } catch (err) {
      alert('PDF generation failed: ' + (err?.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  if (!show) return null;
  return (
    <div className="modal d-block" tabIndex="-1" role="dialog" style={{ backgroundColor: 'rgba(0,0,0,0.4)' }}>
      <div className="modal-dialog modal-lg" role="document">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Generate PDF report</h5>
            <button type="button" className="btn-close" onClick={() => onClose && onClose()} />
          </div>
          <div className="modal-body">
            <div className="mb-2">
              <label className="form-label">Filename</label>
              <input className="form-control form-control-sm" value={filename} onChange={(e) => setFilename(e.target.value)} />
            </div>

            <div className="mb-2">
              <strong>Include</strong>
              <div className="form-check">
                <input className="form-check-input" type="checkbox" checked={includeSummary} onChange={(e) => setIncludeSummary(e.target.checked)} id="incSummary" />
                <label className="form-check-label" htmlFor="incSummary">Summary</label>
              </div>

              <div className="form-check mt-1">
                <input className="form-check-input" type="checkbox" checked={includeTypeChart} onChange={(e) => setIncludeTypeChart(e.target.checked)} id="incTypeChart" />
                <label className="form-check-label" htmlFor="incTypeChart">Type Distribution chart</label>
              </div>

              {includeTypeChart && (
                <div className="ms-3 mb-2">
                  <label className="form-label small mb-1">Type chart style</label>
                  <select className="form-select form-select-sm w-auto" value={typeChartType} onChange={(e) => setTypeChartType(e.target.value)}>
                    {CHART_TYPES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
              )}

              <div className="form-check mt-1">
                <input className="form-check-input" type="checkbox" checked={includeAnalysis} onChange={(e) => setIncludeAnalysis(e.target.checked)} id="incAnalysis" />
                <label className="form-check-label" htmlFor="incAnalysis">Analysis chart(s)</label>
              </div>

              {includeAnalysis && (
                <div className="mt-2 ms-3">
                  <div className="form-check form-check-inline">
                    <input className="form-check-input" type="radio" id="modeSingle" name="mode" checked={analysisMode === 'single'} onChange={() => setAnalysisMode('single')} />
                    <label className="form-check-label" htmlFor="modeSingle">Single</label>
                  </div>
                  <div className="form-check form-check-inline">
                    <input className="form-check-input" type="radio" id="modeMulti" name="mode" checked={analysisMode === 'multi'} onChange={() => setAnalysisMode('multi')} />
                    <label className="form-check-label" htmlFor="modeMulti">Multi</label>
                  </div>

                  {analysisMode === 'single' && (
                    <div className="mt-2">
                      <label className="form-label small">Parameter</label>
                      <select className="form-select form-select-sm w-auto" value={analysisParam} onChange={(e) => setAnalysisParam(e.target.value)}>
                        <option>Flowrate</option>
                        <option>Pressure</option>
                        <option>Temperature</option>
                      </select>
                    </div>
                  )}

                  <div className="mt-2">
                    <label className="form-label small mb-1">Analysis chart style</label>
                    <select className="form-select form-select-sm w-auto" value={analysisChartType} onChange={(e) => setAnalysisChartType(e.target.value)}>
                      {CHART_TYPES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                    <div className="text-muted small mt-1">Chart type applied to analysis chart(s).</div>
                  </div>
                </div>
              )}

              <div className="form-check mt-2">
                <input className="form-check-input" type="checkbox" checked={includePreview} onChange={(e) => setIncludePreview(e.target.checked)} id="incPreview" />
                <label className="form-check-label" htmlFor="incPreview">Data preview (first rows)</label>
              </div>
            </div>

            <div className="text-muted small">
              Choose which sections and chart styles to include. Defaults are sensible.
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={() => onClose && onClose()} disabled={loading}>Cancel</button>
            <button type="button" className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
              {loading ? 'Generating…' : 'Generate & Download'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
