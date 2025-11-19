// src/components/StatsWidget.jsx
import React from 'react';
import styles from '../styles/StatsWidget.module.css';

export default function StatsWidget({ summary = {}, previewRows = [] }) {
  if (!summary) return null;

  const { total_count, averages = {}, type_distribution = {} } = summary;
  const totalTypes = Object.keys(type_distribution).length;

  // Calculate missing counts
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

  return (
    <div className={styles.widgetContainer}>
      {/* Total Records and Total Equipment Types - Two Column Layout */}
      <div className={styles.twoColumnLayout}>
        {/* Total Records */}
        <div className={styles.totalRecordsCard}>
          <div className={styles.totalLabel}>Total Records</div>
          <div className={styles.totalValue}>{total_count}</div>
        </div>

        {/* Total Equipment Types */}
        <div className={styles.totalRecordsCard}>
          <div className={styles.totalLabel}>Equipment Types</div>
          <div className={styles.totalValue}>{totalTypes}</div>
        </div>
      </div>

      {/* Two Column Layout for Averages and Missing Values */}
      <div className={styles.twoColumnLayout}>
        {/* Averages Card */}
        <div className={styles.statsCard}>
          <div className={styles.cardLabel}>Averages</div>
          <div className={styles.averagesList}>
            {averages && Object.entries(averages).map(([key, value]) => (
              <div key={key} className={styles.avgLine}>
                <span className={styles.avgKey}>{key}</span>
                <span className={styles.avgVal}>{value === null ? 'N/A' : Number(value).toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Missing Values Card */}
        <div className={styles.statsCard}>
          <div className={styles.cardLabel}>Missing Values</div>
          <div className={styles.missingList}>
            {numericCols.map((col) => (
              <div key={col} className={styles.missingLine}>
                <span className={styles.missingKey}>{col}</span>
                <span className={styles.missingVal}>
                  {typeof missingCounts[col] === 'number' ? missingCounts[col] : '?'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

