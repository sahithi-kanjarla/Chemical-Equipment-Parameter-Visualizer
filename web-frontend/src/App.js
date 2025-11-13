// src/App.js
import React, { useEffect, useState } from 'react';
import './App.css';
import api, { setAuthToken } from './api';
import UploadForm from './components/UploadForm';
import SummaryPanel from './components/SummaryPanel';
import TypeChart from './components/TypeChart';
import HistoryPanel from './components/HistoryPanel';
import ParameterAnalysisChart from './components/ParameterAnalysisChart';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [currentSummary, setCurrentSummary] = useState(null);
  const [currentDatasetId, setCurrentDatasetId] = useState(null);
  const [chartType, setChartType] = useState('bar');
  const [previewRows, setPreviewRows] = useState([]);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'analysis'

  useEffect(() => {
    setAuthToken(token);
    if (token) localStorage.setItem('token', token);
    else localStorage.removeItem('token');
  }, [token]);

  const onUploaded = (data) => {
    console.log('onUploaded called with:', data);
    if (!data) {
      setCurrentSummary(null);
      setCurrentDatasetId(null);
      setPreviewRows([]);
      return;
    }
    setCurrentSummary(data.summary || null);
    setCurrentDatasetId(data.id || (data.object && data.object.id) || null);
    setPreviewRows(Array.isArray(data.preview_rows) ? data.preview_rows : []);
    // switch to overview so user sees summary/chart after upload
    setActiveTab('overview');
  };

  const loadSummaryById = async (id) => {
    try {
      const res = await api.get(`summary/${id}/`);
      const data = res.data || {};
      const summary = data.summary || data;
      const preview =
        Array.isArray(data.preview_rows) ? data.preview_rows :
        Array.isArray(data.previewRows) ? data.previewRows : [];
      setCurrentSummary(summary);
      setCurrentDatasetId(id);
      setPreviewRows(preview);
      setActiveTab('overview');
    } catch (err) {
      alert(err?.response?.data || err.message);
    }
  };

  const handleTokenSet = () => {
    alert('Token saved (for this browser). Now you can upload and view history.');
  };

  return (
    <div className="container my-4">
      <h2>Chemical Equipment Parameter Visualizer — Web</h2>

      <div className="card p-3 mb-3">
        <div className="row g-2">
          <div className="col-md-8">
            <input
              type="text"
              className="form-control"
              placeholder="Enter API token (Token string only)"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
          </div>
          <div className="col-md-4">
            <button className="btn btn-success w-100" onClick={handleTokenSet}>Save Token</button>
          </div>
          <div className="col-12 mt-2">
            <small className="text-muted">Get a token from /api-token-auth/ or Django admin (Tokens).</small>
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-lg-4">
          <UploadForm onUploaded={onUploaded} />
          <HistoryPanel onSelect={loadSummaryById} />
        </div>

        <div className="col-lg-8">
          {/* Tabs */}
          <ul className="nav nav-tabs mb-3">
            <li className="nav-item">
              <button className={`nav-link ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>Overview</button>
            </li>
            <li className="nav-item">
              <button className={`nav-link ${activeTab === 'analysis' ? 'active' : ''}`} onClick={() => setActiveTab('analysis')}>Analysis</button>
            </li>
          </ul>

          {activeTab === 'overview' && (
            <>
              <SummaryPanel
                summary={currentSummary}
                datasetId={currentDatasetId}
                chartType={chartType}
                setChartType={setChartType}
                previewRows={previewRows}
              />
              <TypeChart
                distribution={currentSummary?.type_distribution}
                summary={currentSummary}
                chartType={chartType}
              />
            </>
          )}

          {activeTab === 'analysis' && (
            <>
              <ParameterAnalysisChart summary={currentSummary} />
              {/* future analysis components (correlation, scatter, trend) go here */}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
