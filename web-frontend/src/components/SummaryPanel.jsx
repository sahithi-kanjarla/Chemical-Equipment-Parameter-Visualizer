// src/components/SummaryPanel.jsx
import React, { useState } from 'react';
import { saveAs } from 'file-saver';
import { downloadReportPdf } from '../api';
import PDFModal from './PDFModal';

const CHART_OPTIONS = [
  { value: 'bar', label: 'Bar (default)' },
  { value: 'pie', label: 'Pie' },
  { value: 'line', label: 'Line' },
  { value: 'hist', label: 'Histogram' },
  { value: 'avg', label: 'Per-type avg (Flowrate)' },
];

export default function SummaryPanel({
  summary,
  datasetId,
  chartType,
  setChartType,
  previewRows = [],
}) {
  const [showPdfModal, setShowPdfModal] = useState(false);

  if (!summary) return null;

  const { total_count, averages, type_distribution } = summary || {};

  const handleDownloadSaved = async () => {
    try {
      if (!datasetId) {
        alert('No datasetId found for saved report.');
        return;
      }
      const blob = await downloadReportPdf(datasetId, chartType);
      const filename = `report_dataset_${datasetId}_${chartType}.pdf`;
      saveAs(blob, filename);
    } catch (err) {
      alert('PDF download failed: ' + (err?.response?.data?.detail || err.message));
    }
  };

  // compute missing counts: prefer using previewRows if provided, else try summary (best-effort)
  const numericCols = ['Flowrate', 'Pressure', 'Temperature'];
  const missingCounts = { Flowrate: 0, Pressure: 0, Temperature: 0 };

  if (previewRows && previewRows.length > 0) {
    previewRows.forEach((r) => {
      numericCols.forEach((c) => {
        const val = r[c];
        if (val === null || val === undefined || String(val).trim() === '') missingCounts[c] += 1;
      });
    });
  } else if (summary && summary.missing_counts) {
    // if backend computed missing_counts earlier
    Object.assign(missingCounts, summary.missing_counts);
  } else {
    // fallback estimate: if averages exist and are null -> imply missing for that numeric col (cannot count rows though)
    numericCols.forEach((c) => {
      if (!averages || averages[c] == null) missingCounts[c] = 'unknown';
    });
  }

  const previewCols = (previewRows && previewRows.length > 0) ? Object.keys(previewRows[0]) : [];

  return (
    <>
      <div className="card p-3 mb-3">
        <div className="d-flex justify-content-between align-items-start mb-2">
          <h5 className="me-3">Summary</h5>
          <div>
            {datasetId && (
              <button className="btn btn-sm btn-primary me-2" onClick={handleDownloadSaved}>
                Download Saved PDF
              </button>
            )}
            <button
              className="btn btn-sm btn-outline-secondary me-2"
              onClick={() => setShowPdfModal(true)}
            >
              Generate PDF
            </button>
          </div>
        </div>

        {/* Chart selector */}
        <div className="mb-3 d-flex align-items-center">
          <label className="me-2 mb-0"><strong>Chart type:</strong></label>
          <select
            className="form-select form-select-sm w-auto"
            value={chartType || 'bar'}
            onChange={(e) => setChartType && setChartType(e.target.value)}
          >
            {CHART_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <small className="text-muted ms-3">This controls the on-screen chart & PDF.</small>
        </div>

        <div className="mb-2 d-flex gap-3 align-items-center">
          <div><strong>Total equipment:</strong> {total_count}</div>
          <div>
            <strong>Missing:</strong>
            <span className="ms-2 text-muted">
              {typeof missingCounts.Flowrate === 'number' ? `Flowrate: ${missingCounts.Flowrate}` : 'Flowrate: ?'}
              {', '}
              {typeof missingCounts.Pressure === 'number' ? `Pressure: ${missingCounts.Pressure}` : 'Pressure: ?'}
              {', '}
              {typeof missingCounts.Temperature === 'number' ? `Temperature: ${missingCounts.Temperature}` : 'Temperature: ?'}
            </span>
          </div>
        </div>

        <div>
          <strong>Averages</strong>
          <ul>
            {averages && Object.entries(averages).map(([k, v]) => (
              <li key={k}>{k}: {v === null ? 'N/A' : Number(v).toFixed(2)}</li>
            ))}
          </ul>
        </div>

        <div>
          <strong>Type Distribution</strong>
          <ul>
            {type_distribution && Object.entries(type_distribution).map(([k, v]) => <li key={k}>{k}: {v}</li>)}
          </ul>
        </div>

        {/* Data preview table */}
        {previewRows && previewRows.length > 0 ? (
          <div className="mt-3">
            <strong>Data preview (first rows)</strong>
            <div className="table-responsive">
              <table className="table table-sm table-striped mt-2">
                <thead>
                  <tr>
                    {previewCols.map((col) => <th key={col}>{col}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {previewRows.map((row, idx) => (
                    <tr key={idx}>
                      {previewCols.map((col) => (
                        <td key={col}>{row[col] === null || row[col] === undefined ? '' : String(row[col])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="mt-3 text-muted">
            <small>No preview rows available. Upload a CSV to see a data preview.</small>
          </div>
        )}
      </div>

      {/* PDF modal */}
      <PDFModal
        show={showPdfModal}
        onClose={() => setShowPdfModal(false)}
        summary={summary}
        previewRows={previewRows}
        defaultFilename={datasetId ? `report_dataset_${datasetId}.pdf` : 'report.pdf'}
      />
    </>
  );
}
