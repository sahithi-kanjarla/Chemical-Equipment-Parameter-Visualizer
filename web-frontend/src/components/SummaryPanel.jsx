// src/components/SummaryPanel.jsx
import React, { useState } from 'react';
import PDFModal from './PDFModal';
import StatsWidget from './StatsWidget';
import TypeChart from './TypeChart';
import styles from '../styles/SummaryPanel.module.css';

export default function SummaryPanel({
  summary,
  datasetId,
  chartType,
  setChartType,
  previewRows = [],
  analysisChartTypes = {},
}) {
  const [showPdfModal, setShowPdfModal] = useState(false);

  if (!summary) return null;

  const { total_count, averages, type_distribution } = summary || {};

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
    Object.assign(missingCounts, summary.missing_counts);
  } else {
    numericCols.forEach((c) => {
      if (!averages || averages[c] == null) missingCounts[c] = 'unknown';
    });
  }

  const previewCols = (previewRows && previewRows.length > 0) ? Object.keys(previewRows[0]) : [];

  return (
    <>
      <div className={styles.card}>
        <div className={styles.header}>
          <h5 className={styles.title}>Summary</h5>
          <div>
            {/* SINGLE Generate PDF button (opens modal). */}
            <button className={styles.btnPrimary} onClick={() => setShowPdfModal(true)}>
              Generate PDF
            </button>
          </div>
        </div>

        <StatsWidget summary={summary} previewRows={previewRows} />

        {/* Type Distribution Chart */}
        <div className={styles.chartSection}>
          <TypeChart
            distribution={type_distribution}
            summary={summary}
            chartType={chartType}
            onChartTypeChange={setChartType}
          />
        </div>

        {/* Data Preview */}
        {previewRows && previewRows.length > 0 ? (
          <div className={styles.tableSection}>
            <strong>Data preview (first rows)</strong>
            <div className={styles.tableResponsive}>
              <table className={styles.table}>
                <thead>
                  <tr>{previewCols.map((col) => <th key={col}>{col}</th>)}</tr>
                </thead>
                <tbody>
                  {previewRows.map((row, idx) => (
                    <tr key={idx}>{previewCols.map((col) => <td key={col}>{row[col] === null || row[col] === undefined ? '' : String(row[col])}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className={styles.noPreview}><small>No preview rows available. Upload a CSV to see a preview.</small></div>
        )}
      </div>

      <PDFModal
        show={showPdfModal}
        onClose={() => setShowPdfModal(false)}
        summary={summary}
        previewRows={previewRows}
        defaultFilename={datasetId ? `report_dataset_${datasetId}.pdf` : 'report.pdf'}
        datasetId={datasetId}
        overviewChartType={chartType}
        analysisChartTypes={analysisChartTypes}
      />
    </>
  );
}
