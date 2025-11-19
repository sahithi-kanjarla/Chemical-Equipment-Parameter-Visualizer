// src/App.js
import React, { useEffect, useState } from 'react';
import './App.css';
import api, { login as apiLogin, logout as apiLogout, getAccessToken, setAccessToken } from './api';
import UploadForm from './components/UploadForm';
import SummaryPanel from './components/SummaryPanel';
import TypeChart from './components/TypeChart';
import HistoryPanel from './components/HistoryPanel';
import ParameterAnalysisChart from './components/ParameterAnalysisChart';
import Header from './components/Header';
import LoginPanel from './components/LoginPanel';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [accessToken, setTokenState] = useState(getAccessToken() || null);
  const [username, setUsername] = useState(null);

  const [currentSummary, setCurrentSummary] = useState(null);
  const [currentDatasetId, setCurrentDatasetId] = useState(null);
  const [overviewChartType, setOverviewChartType] = useState('bar');
  const [analysisChartTypes, setAnalysisChartTypes] = useState({ Flowrate: 'bar', Pressure: 'bar', Temperature: 'bar' });
  const [removedCharts, setRemovedCharts] = useState(new Set());
  const [previewRows, setPreviewRows] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (accessToken) {
      api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
      setTokenState(accessToken);
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  }, [accessToken]);

  const onUploaded = (data) => {
    if (!data) return;
    setCurrentSummary(data.summary || null);
    setCurrentDatasetId(data.id || (data.object && data.object.id) || null);
    setPreviewRows(Array.isArray(data.preview_rows) ? data.preview_rows : []);
    setActiveTab('overview');
    setRemovedCharts(new Set());
  };

  const loadSummaryById = async (id) => {
    try {
      const res = await api.get(`summary/${id}/`);
      const data = res.data || {};
      const summary = data.summary || data;
      const preview = Array.isArray(data.preview_rows) ? data.preview_rows : (Array.isArray(data.previewRows) ? data.previewRows : []);
      setCurrentSummary(summary);
      setCurrentDatasetId(id);
      setPreviewRows(preview);
      setActiveTab('overview');
      setRemovedCharts(new Set());
    } catch (err) {
      alert(err?.response?.data || err.message);
    }
  };

  const handleLogin = async (u, p) => {
    try {
      const tokens = await apiLogin(u, p);
      setTokenState(tokens.access);
      setUsername(u);
    } catch (err) {
      alert('Login failed: ' + (err?.response?.data?.detail || err.message));
    }
  };
  const handleLogout = () => {
    apiLogout();
    setTokenState(null);
    setUsername(null);
    setCurrentSummary(null);
    setCurrentDatasetId(null);
    setPreviewRows([]);
    setRemovedCharts(new Set());
  };

  function updateAnalysisChartType(param, newType) {
    setAnalysisChartTypes(prev => ({ ...prev, [param]: newType }));
  }
  function removeAnalysisChart(param) {
    setRemovedCharts(prev => new Set(Array.from(prev).concat([param])));
  }
  function restoreAnalysisChart(param) {
    setRemovedCharts(prev => {
      const s = new Set(Array.from(prev));
      s.delete(param);
      return s;
    });
  }

  return (
    <>
      {accessToken && <Header username={username} onLogout={handleLogout} />}
      
      {!accessToken ? (
        <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '100vh' }}>
          <LoginPanel onLogin={handleLogin} />
        </div>
      ) : (
        <div className="container my-4">
          <div className="row">
            <div className="col-lg-4">
              <UploadForm onUploaded={onUploaded} disabled={!accessToken} />
              <HistoryPanel onSelect={loadSummaryById} />
            </div>

            <div className="col-lg-8">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <ul className="nav nav-tabs">
              <li className="nav-item">
                <button className={`nav-link ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>Overview</button>
              </li>
              <li className="nav-item">
                <button className={`nav-link ${activeTab === 'analysis' ? 'active' : ''}`} onClick={() => setActiveTab('analysis')}>Analysis</button>
              </li>
            </ul>
          </div>

          {activeTab === 'overview' && (
            <>
              <SummaryPanel
                summary={currentSummary}
                datasetId={currentDatasetId}
                chartType={overviewChartType}
                setChartType={setOverviewChartType}
                previewRows={previewRows}
                analysisChartTypes={analysisChartTypes}
              />
            </>
          )}

          {activeTab === 'analysis' && (
            <>
              <ParameterAnalysisChart
                summary={currentSummary}
                analysisChartTypes={analysisChartTypes}
                onChangeChartType={updateAnalysisChartType}
                onRemoveChart={removeAnalysisChart}
                removedCharts={Array.from(removedCharts)}
                onRestoreChart={restoreAnalysisChart}
              />
            </>
          )}
        </div>
      </div>
        </div>
      )}
    </>
  );
}

export default App;
