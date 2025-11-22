// src/components/LoginPanel.jsx
import React, { useState } from 'react';
import { login } from '../api';
import styles from '../styles/LoginPanel.module.css';
import logo from '../assets/logo.png.png'; // <-- import your logo

export default function LoginPanel({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e) => {
    e && e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const tokens = await login(username.trim(), password);
      setUsername('');
      setPassword('');
      if (onLogin) onLogin(username.trim(), password);
    } catch (err) {
      const errorMessage = err?.response?.data?.detail || err.message || 'Login failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.loginPageWrapper}>
      <div className={styles.loginCard}>

        {/* Logo Section */}
        <div className={styles.logoSection}>
          <img src={logo} alt="App Logo" className={styles.logoImage} />
        </div>

        {/* Title Section */}
        <div className={styles.titleSection}>
          <h1 className={styles.title}>Chemical Equipment</h1>
          <p className={styles.subtitle}>Parameter Visualizer</p>
        </div>

        {/* Welcome Message */}
        <p className={styles.welcomeText}>Sign in to your account</p>

        {/* Error Message */}
        {error && <div className={styles.errorMessage}>{error}</div>}

        {/* Login Form */}
        <form className={styles.loginForm} onSubmit={submit}>
          <div className={styles.formGroup}>
            <label className={styles.label}>Username</label>
            <input
              className={styles.inputField}
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Password</label>
            <input
              className={styles.inputField}
              placeholder="Enter your password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button className={styles.loginButton} disabled={loading} type="submit">
            {loading ? (
              <>
                <span className={styles.spinner}></span>
                Logging in…
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
