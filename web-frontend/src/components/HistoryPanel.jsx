// src/components/HistoryPanel.jsx
import React, { useEffect, useState } from 'react';
import api from '../api';
import styles from '../styles/HistoryPanel.module.css';

export default function HistoryPanel({ onSelect }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('history/');
      setHistory(res.data || []);
    } catch (err) {
      setError(err?.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className={styles.historyPanel}>
      <div className={styles.header}>
        <div className={styles.titleSection}>
          <h5 className={styles.title}>Upload History</h5>
          <p className={styles.subtitle}>Last 5 uploads</p>
        </div>
        <button className={styles.refreshButton} onClick={fetchHistory} disabled={loading}>
          {loading ? (
            <>
              <span className={styles.spinner}></span>
              Loading
            </>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 2.2" />
              </svg>
              Refresh
            </>
          )}
        </button>
      </div>

      {loading && !history.length && <div className={styles.loadingState}>Loading history...</div>}
      {error && <div className={styles.errorMessage}>{JSON.stringify(error)}</div>}

      {history.length === 0 && !loading && (
        <div className={styles.emptyState}>
          <p>No uploads yet. Upload a CSV file to get started.</p>
        </div>
      )}

      <div className={styles.historyList}>
        {history.map((item, index) => (
          <div className={styles.historyItem} key={item.id}>
            <div className={styles.itemNumber}>{index + 1}</div>
            <div className={styles.itemContent}>
              <div className={styles.filename}>{item.original_filename}</div>
              <div className={styles.timestamp}>{formatDate(item.uploaded_at)}</div>
            </div>
            <div className={styles.itemActions}>
              <button className={styles.loadButton} onClick={() => onSelect(item.id)}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 14c1.49-1.46 3-3.59 3-5.68C22 5.92 19.57 3 16.5 3 14.64 3 13 4.05 12 5.65 11 4.05 9.36 3 7.5 3 4.43 3 2 5.92 2 8.32c0 2.09 1.51 4.22 3 5.68" />
                  <path d="M12 17c-.5-.5-1-1.2-1-2 0-1.1.9-2 2-2s2 .9 2 2c0 .8-.5 1.5-1 2m0 3v2" />
                </svg>
                Load
              </button>
              {item.csv_file && (
                <a className={styles.downloadButton} href={item.csv_file} target="_blank" rel="noreferrer">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  CSV
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
