// src/components/Header.jsx
import React, { useState, useRef, useEffect } from "react";
import styles from "../styles/Header.module.css";
import { useAuth } from "../auth/AuthContext";

export default function Header() {
  const { user, logout } = useAuth();                        // ⬅ From context
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // initials for avatar
  const initials = user
    ? user
        .split(" ")
        .map((part) => part[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  const avatarColor = generateColorFromString(user || "user");

  // close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    setShowDropdown(false);
    logout();                                                // ⬅ logout directly
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
                  <span className={styles.dropdownUsername}>{user || "User"}</span>
                  <span className={styles.dropdownEmail}>Logged in</span>
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

// Generate consistent avatar color
function generateColorFromString(str) {
  const colors = [
    "#5B7C99", "#4A6FA5", "#627BA7", "#6B5B95",
    "#5A7C6B", "#5A7F8C", "#7B6B5B", "#6B7F5B",
  ];

  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}
