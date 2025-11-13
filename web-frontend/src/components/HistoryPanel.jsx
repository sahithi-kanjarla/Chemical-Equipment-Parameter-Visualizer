// src/components/HistoryPanel.jsx
import React, { useEffect, useState } from 'react';
import api from '../api';

export default function HistoryPanel({ onSelect }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('history/');
      setHistory(res.data);
    } catch (err) {
      setError(err?.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchHistory(); }, []);

  return (
    <div className="card p-3 mb-3">
      <div className="d-flex justify-content-between align-items-center">
        <h5>History (last 5)</h5>
        <button className="btn btn-sm btn-outline-secondary" onClick={fetchHistory}>Refresh</button>
      </div>

      {loading && <p>Loading...</p>}
      {error && <div className="text-danger">{JSON.stringify(error)}</div>}
      <ul className="list-group mt-2">
        {history.map((h) => (
          <li className="list-group-item d-flex justify-content-between align-items-center" key={h.id}>
            <div>
              <strong>{h.original_filename}</strong>
              <div><small>{new Date(h.uploaded_at).toLocaleString()}</small></div>
            </div>
            <div>
              <button className="btn btn-sm btn-primary me-2" onClick={() => onSelect(h.id)}>Load</button>
              <a className="btn btn-sm btn-outline-secondary" href={h.csv_file} target="_blank" rel="noreferrer">CSV</a>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
