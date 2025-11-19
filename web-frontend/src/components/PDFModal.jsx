// src/components/PDFModal.jsx
import React, { useState, useEffect } from 'react';
import api from '../api';
import styles from '../styles/PDFModal.module.css';

const DEFAULT_FILENAME = 'report.pdf';

export default function PDFModal({
  show,
  onClose,
  summary,
  previewRows,
  defaultFilename = DEFAULT_FILENAME,
  datasetId = null,
  overviewChartType = 'bar',
  analysisChartTypes = {},
  removedCharts = [],
}) {
  const [includeSummary, setIncludeSummary] = useState(true);
  const [includeTypeChart, setIncludeTypeChart] = useState(true);
  const [includeAnalysis, setIncludeAnalysis] = useState(true);
  const [includePreview, setIncludePreview] = useState(true);
  const [filename, setFilename] = useState(defaultFilename);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setFilename(defaultFilename || DEFAULT_FILENAME);
  }, [defaultFilename]);

  if (!show) return null;

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const payload = {
        filename: filename || DEFAULT_FILENAME,
        include: {
          summary: includeSummary,
          type_chart: includeTypeChart,
          analysis: {
            include: includeAnalysis,
            mode: 'all',
          },
          preview_rows: includePreview,
          type_chart_type: overviewChartType,
        },
        removed_charts: Array.isArray(removedCharts) ? removedCharts : Array.from(removedCharts || []),
        summary: summary || {},
        preview_rows: includePreview ? (previewRows || []) : [],
        overview_chart_type: overviewChartType || 'bar',
        analysis_chart_types: analysisChartTypes || {},
      };

      const res = await api.post('report-from-summary/', payload, { responseType: 'blob' });
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || DEFAULT_FILENAME;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      onClose && onClose();
    } catch (err) {
      alert('PDF generation failed: ' + (err?.response?.data?.detail || err.message));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.pdfModalOverlay}>
      <div className={styles.pdfModalContent}>
        <div className={styles.pdfModalHeader}>
          <h5 className={styles.pdfModalTitle}>Generate PDF Report</h5>
          <button type="button" className={styles.closeButton} onClick={() => onClose && onClose()}>✕</button>
        </div>
        <div className={styles.pdfModalBody}>
          <div className={styles.optionGroup}>
            <label className={styles.optionLabel} style={{ marginBottom: '12px' }}>
              <span style={{ fontWeight: '600', color: '#333' }}>Filename</span>
            </label>
            <input 
              style={{ width: '100%', padding: '10px 12px', border: '2px solid #007bff', borderRadius: '6px', fontSize: '14px' }}
              value={filename} 
              onChange={(e) => setFilename(e.target.value)} 
            />
          </div>

          <div className={styles.optionGroup}>
            <strong style={{ fontSize: '15px', color: '#333', marginBottom: '12px', display: 'block' }}>Include in PDF</strong>
            
            <label className={styles.optionLabel}>
              <input 
                className={styles.checkbox}
                type="checkbox" 
                checked={includeSummary} 
                onChange={(e) => setIncludeSummary(e.target.checked)} 
              />
              <span>Summary</span>
            </label>

            <label className={styles.optionLabel}>
              <input 
                className={styles.checkbox}
                type="checkbox" 
                checked={includeTypeChart} 
                onChange={(e) => setIncludeTypeChart(e.target.checked)} 
              />
              <span>Type Distribution Chart</span>
            </label>

            <label className={styles.optionLabel}>
              <input 
                className={styles.checkbox}
                type="checkbox" 
                checked={includeAnalysis} 
                onChange={(e) => setIncludeAnalysis(e.target.checked)} 
              />
              <span>Analysis Charts</span>
            </label>

            <label className={styles.optionLabel}>
              <input 
                className={styles.checkbox}
                type="checkbox" 
                checked={includePreview} 
                onChange={(e) => setIncludePreview(e.target.checked)} 
              />
              <span>Data Preview (first rows)</span>
            </label>
          </div>

          <div style={{ color: '#666', fontSize: '13px', fontStyle: 'italic', marginTop: '16px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
            ℹ️ The PDF will use the chart types you selected in the Overview and Analysis views. Removed charts will be skipped.
          </div>
        </div>

        <div className={styles.pdfModalFooter}>
          <button type="button" className={styles.cancelButton} onClick={() => onClose && onClose()} disabled={loading}>Cancel</button>
          <button type="button" className={styles.downloadButton} onClick={handleGenerate} disabled={loading}>
            {loading ? 'Generating…' : 'Generate & Download'}
          </button>
        </div>
      </div>
    </div>
  );
}
