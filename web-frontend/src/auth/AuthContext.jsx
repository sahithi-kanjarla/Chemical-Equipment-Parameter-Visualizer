// src/auth/AuthContext.jsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import api, { login as apiLogin, logout as apiLogout, getAccessToken, getRefreshToken, setAccessToken, setTokens, clearTokens } from '../api';

// Context + hook
const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(getAccessToken()));
  const [user, setUser] = useState(null); // optionally store username

  useEffect(() => {
    // If access token exists, mark authenticated.
    if (getAccessToken()) {
      setIsAuthenticated(true);
      // We don't have user details from token in this app; if you want you can decode JWT to get username/email.
    } else {
      setIsAuthenticated(false);
      setUser(null);
    }
  }, []);

  async function login(username, password) {
    // call api.login (this will persist tokens and set Authorization header)
    try {
      const data = await apiLogin(username, password);
      // api.login already calls setTokens() and sets header; mark state
      setIsAuthenticated(true);
      setUser(username || null);
      return { ok: true, data };
    } catch (err) {
      // ensure tokens cleared on failure
      try { clearTokens(); } catch (e) {}
      setIsAuthenticated(false);
      setUser(null);
      const message = err?.response?.data || err?.message || String(err);
      return { ok: false, error: message };
    }
  }

  function logout() {
    // clear tokens and call optional server-side logout if you have one
    try {
      apiLogout();
    } catch (e) { /* ignore */ }
    clearTokens();
    setAccessToken(null);
    setIsAuthenticated(false);
    setUser(null);
  }

  // allow manually set access token (useful for dev/testing)
  function setAccess(accessToken) {
    try {
      setAccessToken(accessToken);
      if (accessToken) {
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
    } catch (e) {}
  }

  const value = {
    isAuthenticated,
    user,
    login,
    logout,
    setAccess,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
