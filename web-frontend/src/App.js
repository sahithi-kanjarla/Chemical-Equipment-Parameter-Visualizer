// src/App.js
import React, { useState } from 'react';
import './App.css';
import api from './api';
import UploadForm from './components/UploadForm';
import SummaryPanel from './components/SummaryPanel';
import HistoryPanel from './components/HistoryPanel';
import ParameterAnalysisChart from './components/ParameterAnalysisChart';
import Header from './components/Header';
import LoginPanel from './components/LoginPanel';
import 'bootstrap/dist/css/bootstrap.min.css';

// 🔹 useAuth from your AuthContext
import { useAuth } from './auth/AuthContext';

function App() {
  // ---- Auth state from context ----
  const { isAuthenticated, user, login, logout } = useAuth();

  // ---- App data state (dataset, charts, etc.) ----
  const [currentSummary, setCurrentSummary] = useState(null);
  const [currentDatasetId, setCurrentDatasetId] = useState(null);
  const [overviewChartType, setOverviewChartType] = useState('bar');
  const [analysisChartTypes, setAnalysisChartTypes] = useState({
    Flowrate: 'bar',
    Pressure: 'bar',
    Temperature: 'bar',
  });
  const [removedCharts, setRemovedCharts] = useState(new Set());
  const [previewRows, setPreviewRows] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');

  // When upload completes successfully
  const onUploaded = (data) => {
    if (!data) return;
    setCurrentSummary(data.summary || null);
    setCurrentDatasetId(data.id || (data.object && data.object.id) || null);
    setPreviewRows(Array.isArray(data.preview_rows) ? data.preview_rows : []);
    setActiveTab('overview');
    setRemovedCharts(new Set());
  };

  // Load summary by dataset id (from history)
  const loadSummaryById = async (id) => {
    try {
      const res = await api.get(`summary/${id}/`);
      const data = res.data || {};
      const summary = data.summary || data;
      const preview = Array.isArray(data.preview_rows)
        ? data.preview_rows
        : Array.isArray(data.previewRows)
        ? data.previewRows
        : [];
      setCurrentSummary(summary);
      setCurrentDatasetId(id);
      setPreviewRows(preview);
      setActiveTab('overview');
      setRemovedCharts(new Set());
    } catch (err) {
      alert(err?.response?.data || err.message);
    }
  };

  // Handle login via AuthContext
  const handleLogin = async (u, p) => {
    const result = await login(u, p);
    if (!result.ok) {
      const msg =
        typeof result.error === 'string'
          ? result.error
          : result.error?.detail || JSON.stringify(result.error);
      alert('Login failed: ' + msg);
    }
    // If ok, AuthContext will set isAuthenticated + user
  };

  // Handle logout via AuthContext
  const handleLogout = () => {
    logout();
    // Clear dataset-related state
    setCurrentSummary(null);
    setCurrentDatasetId(null);
    setPreviewRows([]);
    setRemovedCharts(new Set());
    setActiveTab('overview');
  };

  // Chart controls
  function updateAnalysisChartType(param, newType) {
    setAnalysisChartTypes((prev) => ({ ...prev, [param]: newType }));
  }

  function removeAnalysisChart(param) {
    setRemovedCharts((prev) => new Set([...prev, param]));
  }

  function restoreAnalysisChart(param) {
    setRemovedCharts((prev) => {
      const copy = new Set(prev);
      copy.delete(param);
      return copy;
    });
  }

  return (
    <>
      {/* Header only when logged in */}
      {isAuthenticated && <Header username={user} onLogout={handleLogout} />}

      {/* If not authenticated -> show Login panel full-screen */}
      {!isAuthenticated ? (
        <div
          className="d-flex justify-content-center align-items-center"
          style={{ minHeight: '100vh' }}
        >
          <LoginPanel onLogin={handleLogin} />
        </div>
      ) : (
        // Main app layout
        <div className="container my-4">
          <div className="row">
            {/* Left column: upload + history */}
            <div className="col-lg-4">
              <UploadForm onUploaded={onUploaded} disabled={!isAuthenticated} />
              <HistoryPanel onSelect={loadSummaryById} />
            </div>

            {/* Right column: tabs + panels */}
            <div className="col-lg-8">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <ul className="nav nav-tabs">
                  <li className="nav-item">
                    <button
                      className={`nav-link ${
                        activeTab === 'overview' ? 'active' : ''
                      }`}
                      onClick={() => setActiveTab('overview')}
                    >
                      Overview
                    </button>
                  </li>
                  <li className="nav-item">
                    <button
                      className={`nav-link ${
                        activeTab === 'analysis' ? 'active' : ''
                      }`}
                      onClick={() => setActiveTab('analysis')}
                    >
                      Analysis
                    </button>
                  </li>
                </ul>
              </div>

              {activeTab === 'overview' && (
                <SummaryPanel
                  summary={currentSummary}
                  datasetId={currentDatasetId}
                  chartType={overviewChartType}
                  setChartType={setOverviewChartType}
                  previewRows={previewRows}
                  analysisChartTypes={analysisChartTypes}
                />
              )}

              {activeTab === 'analysis' && (
                <ParameterAnalysisChart
                  summary={currentSummary}
                  analysisChartTypes={analysisChartTypes}
                  onChangeChartType={updateAnalysisChartType}
                  onRemoveChart={removeAnalysisChart}
                  removedCharts={[...removedCharts]}
                  onRestoreChart={restoreAnalysisChart}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default App;
