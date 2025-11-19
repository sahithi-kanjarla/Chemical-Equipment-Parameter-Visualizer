// src/api.js
import axios from 'axios';
import { API_BASE } from './config';

// normalize API root
const API_ROOT = (API_BASE || '').replace(/\/+$/, '') + '/api/';

const api = axios.create({
  baseURL: API_ROOT,
  // callers may set timeout per request
});

// localStorage keys
const ACCESS_KEY = 'cepv_access';
const REFRESH_KEY = 'cepv_refresh';

// --- token helpers ---
export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}
export function setAccessToken(token) {
  if (token) {
    localStorage.setItem(ACCESS_KEY, token);
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    localStorage.removeItem(ACCESS_KEY);
    delete api.defaults.headers.common['Authorization'];
  }
}
export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  if (access) api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
}
export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  delete api.defaults.headers.common['Authorization'];
}

// init header if token exists
const initialAccess = getAccessToken();
if (initialAccess) api.defaults.headers.common['Authorization'] = `Bearer ${initialAccess}`;

// --- token refresh queue to avoid parallel refreshes ---
let isRefreshing = false;
let refreshSubscribers = [];

function subscribeRefresh(cb) {
  refreshSubscribers.push(cb);
}
function onRefreshed(token) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

// refresh access token using refresh token endpoint
export async function refreshToken() {
  const refresh = getRefreshToken();
  if (!refresh) throw new Error('No refresh token');
  const url = `token/refresh/`;
  const resp = await axios.post(API_ROOT + url, { refresh });
  const newAccess = resp.data && resp.data.access;
  if (!newAccess) throw new Error('Refresh did not return access token');
  setAccessToken(newAccess);
  return newAccess;
}

// axios interceptor to handle 401 and refresh
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;
    if (!error.response) return Promise.reject(error);
    if (error.response.status !== 401) return Promise.reject(error);

    // don't try refreshing for token endpoints
    if (originalRequest && originalRequest.url && originalRequest.url.includes('/token/')) {
      clearTokens();
      return Promise.reject(error);
    }

    if (originalRequest._retry) {
      clearTokens();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // queue request until refresh completes
      return new Promise((resolve, reject) => {
        subscribeRefresh((token) => {
          if (!token) return reject(new Error('Refresh failed'));
          originalRequest._retry = true;
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          resolve(api(originalRequest));
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;
    try {
      const newAccess = await refreshToken();
      onRefreshed(newAccess);
      originalRequest.headers['Authorization'] = 'Bearer ' + newAccess;
      return api(originalRequest);
    } catch (err) {
      onRefreshed(null);
      clearTokens();
      return Promise.reject(err);
    } finally {
      isRefreshing = false;
    }
  }
);

// --- public auth helpers ---
/**
 * login(username, password) => { access, refresh }
 * stores tokens on success and sets Authorization header
 */
export async function login(username, password) {
  const resp = await api.post('token/', { username, password });
  const data = resp.data || {};
  const access = data.access;
  const refresh = data.refresh;
  if (!access || !refresh) throw new Error('Login did not return tokens');
  setTokens({ access, refresh });
  return { access, refresh };
}

/**
 * logout(): clears tokens
 */
export function logout() {
  clearTokens();
}

// --- helper endpoints used by UI ---
export async function downloadReportPdf(pk, chartType = 'bar') {
  if (!pk) throw new Error('Dataset id (pk) is required');
  const res = await api.get(`report/${pk}/`, {
    params: { chart_type: chartType },
    responseType: 'blob',
  });
  return res.data;
}

export async function downloadReportFromSummary(summaryObj = {}, previewRows = [], filename = 'report.pdf', chartType = 'bar') {
  const payload = {
    summary: summaryObj || {},
    preview_rows: previewRows || [],
    filename,
    include: { type_chart: true, summary: true, preview_rows: true },
    overview_chart_type: chartType,
  };
  const res = await api.post('report-from-summary/', payload, { responseType: 'blob' });
  return res.data;
}

export default api;
