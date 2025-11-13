// src/api.js
import axios from 'axios';
import { API_BASE } from './config';

const api = axios.create({
  baseURL: API_BASE + '/api/',
  // Authorization header will be set by setAuthToken()
});

/**
 * Set or clear the Authorization header for subsequent requests.
 * Token format used by DRF: "Token <key>"
 */
export function setAuthToken(token) {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Token ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
}

/**
 * Download a stored report PDF by dataset primary key (id).
 * Accepts optional chartType to control which chart is embedded in the PDF.
 * Returns a Blob.
 */
export async function downloadReportPdf(pk, chartType = 'bar') {
  if (!pk) throw new Error('Dataset id (pk) is required');
  const res = await api.get(`report/${pk}/`, {
    params: { chart_type: chartType },
    responseType: 'blob',
  });
  return res.data; // Blob
}

/**
 * Generate and download an ad-hoc report from a summary object (no saved id required).
 * - summaryObj: the summary JSON (total_count, averages, type_distribution)
 * - previewRows: optional array of row objects for a small preview table
 * - filename: optional filename for the downloaded PDF
 * - chartType: 'bar' | 'pie' | 'line' | 'hist'
 *
 * Returns a Blob.
 */
export async function downloadReportFromSummary(
  summaryObj = {},
  previewRows = [],
  filename = 'report.pdf',
  chartType = 'bar'
) {
  const payload = {
    summary: summaryObj || {},
    preview_rows: previewRows || [],
    filename,
    chart_type: chartType,
  };

  const res = await api.post('report-from-summary/', payload, { responseType: 'blob' });
  return res.data; // Blob
}

export default api;
