// src/components/Header.jsx
import React, { useState, useRef, useEffect } from 'react';
import styles from '../styles/Header.module.css';

export default function Header({ username, onLogout }) {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // Generate avatar with initials
  const initials = username
    ? username
        .split(' ')
        .map((part) => part[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U';

  const avatarColor = generateColorFromString(username || 'user');

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    setShowDropdown(false);
    onLogout();
  };

  return (
    <header className={styles.header}>
      <div className={styles.headerContent}>
        {/* Logo and Title */}
        <div className={styles.logoSection}>
          <div className={styles.logoIcon}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
          </div>
          <div className={styles.titleSection}>
            <h1 className={styles.title}>Chemical Equipment</h1>
            <p className={styles.subtitle}>Parameter Visualizer</p>
          </div>
        </div>

        {/* User Profile Dropdown */}
        <div className={styles.profileDropdown} ref={dropdownRef}>
          <button
            className={styles.avatarButton}
            onClick={() => setShowDropdown(!showDropdown)}
            style={{ backgroundColor: avatarColor }}
          >
            {initials}
          </button>

          {showDropdown && (
            <div className={styles.dropdownMenu}>
              <div className={styles.dropdownHeader}>
                <div className={styles.dropdownAvatar} style={{ backgroundColor: avatarColor }}>
                  {initials}
                </div>
                <div className={styles.dropdownUserInfo}>
                  <span className={styles.dropdownUsername}>{username || 'User'}</span>
                  <span className={styles.dropdownEmail}>logged in</span>
                </div>
              </div>
              <div className={styles.dropdownDivider}></div>
              <button className={styles.dropdownLogout} onClick={handleLogout}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M10 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4" />
                  <polyline points="17 16 21 12 17 8" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

// Helper function to generate consistent color from string
function generateColorFromString(str) {
  const colors = [
    '#5B7C99', // Slate Blue
    '#4A6FA5', // Cerulean
    '#627BA7', // Steel Blue
    '#6B5B95', // Muted Purple
    '#5A7C6B', // Sage Green
    '#5A7F8C', // Teal
    '#7B6B5B', // Taupe
    '#6B7F5B', // Olive
  ];

  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}
