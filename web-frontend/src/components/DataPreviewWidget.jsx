// src/components/DataPreviewWidget.jsx
import React from 'react';
import styles from '../styles/DataPreviewWidget.module.css';

export default function DataPreviewWidget({ data, loading = false }) {
  if (!data || !data.summary) return null;

  const { summary, previewRows = [] } = data;
  const { total_count, averages = {}, type_distribution = {} } = summary;

  if (loading) {
    return (
      <div className={styles.widgetContainer}>
        <div className={styles.loadingSpinner}>
          <div className={styles.spinner}></div>
          <p>Loading preview...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.widgetContainer}>
      <h5 className={styles.widgetTitle}>Data Preview</h5>

      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>Total Records</div>
          <div className={styles.statValue}>{total_count}</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statLabel}>Equipment Types</div>
          <div className={styles.statValue}>{Object.keys(type_distribution).length}</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statLabel}>Columns</div>
          <div className={styles.statValue}>{previewRows.length > 0 ? Object.keys(previewRows[0]).length : 0}</div>
        </div>
      </div>

      {previewRows.length > 0 && (
        <div className={styles.tableSection}>
          <h6 className={styles.sectionTitle}>Sample Data</h6>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  {Object.keys(previewRows[0]).map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewRows.slice(0, 5).map((row, idx) => (
                  <tr key={idx}>
                    {Object.keys(previewRows[0]).map((col) => (
                      <td key={col}>{row[col] === null || row[col] === undefined ? '-' : String(row[col]).substring(0, 30)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {previewRows.length > 5 && <p className={styles.moreText}>+{previewRows.length - 5} more rows</p>}
        </div>
      )}

      {Object.keys(averages).length > 0 && (
        <div className={styles.statsSection}>
          <h6 className={styles.sectionTitle}>Averages</h6>
          <div className={styles.avgGrid}>
            {Object.entries(averages).map(([key, value]) => (
              <div key={key} className={styles.avgItem}>
                <span className={styles.avgLabel}>{key}:</span>
                <span className={styles.avgValue}>{value === null ? 'N/A' : Number(value).toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
