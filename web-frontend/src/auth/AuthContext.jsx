// src/auth/AuthContext.jsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import api, {
  login as apiLogin,
  logout as apiLogout,
  getAccessToken,
  clearTokens,
  setAccessToken,
} from '../api';

// Create context + hook
const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(getAccessToken()));
  const [user, setUser] = useState(null);      // store username
  const [loading, setLoading] = useState(true); // loading initial auth state

  // On first mount: if token exists, ask backend who the user is (`/api/me/`)
  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setIsAuthenticated(false);
      setUser(null);
      setLoading(false);
      return;
    }

    // We have a token, assume authenticated until proven otherwise
    setIsAuthenticated(true);

    (async () => {
      try {
        // Backend endpoint must exist: GET /api/me/
        const res = await api.get('me/');
        const username = res?.data?.username || null;
        setUser(username);
      } catch (err) {
        console.error('Failed to load current user from /api/me/', err);
        // Token might be invalid/expired → clear and reset auth state
        try {
          clearTokens();
          setAccessToken(null);
        } catch (e) {
          // ignore
        }
        setIsAuthenticated(false);
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Login with username/password
  async function login(username, password) {
    try {
      const data = await apiLogin(username, password); // this sets tokens + Authorization header
      setIsAuthenticated(true);
      // For now, just trust the username entered. (Optionally call /api/me/ again.)
      setUser(username || null);
      return { ok: true, data };
    } catch (err) {
      try {
        clearTokens();
        setAccessToken(null);
      } catch (e) {
        // ignore
      }
      setIsAuthenticated(false);
      setUser(null);
      const message = err?.response?.data || err?.message || String(err);
      return { ok: false, error: message };
    }
  }

  // Logout: clear tokens + reset state
  function logout() {
    try {
      apiLogout();
    } catch (e) {
      // ignore
    }
    clearTokens();
    setAccessToken(null);
    setIsAuthenticated(false);
    setUser(null);
  }

  // Optional: manually set access token (dev/testing)
  function setAccess(accessToken) {
    try {
      setAccessToken(accessToken);
      if (accessToken) {
        setIsAuthenticated(true);
        // After manually setting, you could also call /api/me/ again if needed
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (e) {
      console.error('Failed to set access token', e);
    }
  }

  const value = {
    isAuthenticated,
    user,      // username string or null
    loading,   // can be used in Navbar to avoid flicker
    login,
    logout,
    setAccess,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
