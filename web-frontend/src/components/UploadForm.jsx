// src/components/UploadForm.jsx
import React, { useState } from 'react';
import api from '../api';
import DataPreviewWidget from './DataPreviewWidget';
import styles from '../styles/UploadForm.module.css';

export default function UploadForm({ onUploaded, disabled = false }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadedData, setUploadedData] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files && e.target.files[0] ? e.target.files[0] : null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      alert('Please choose a CSV file first.');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    try {
      setLoading(true);
      const res = await api.post('upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });
      if (onUploaded) onUploaded(res.data);
      setUploadedData(res.data);
      alert('Upload successful — summary loaded.');
      setFile(null);
      // clear file input visually (if necessary)
      const el = document.getElementById('upload-input');
      if (el) el.value = '';
    } catch (err) {
      console.error('Upload failed', err);
      const msg = err?.response?.data?.detail || err?.message || 'Upload failed';
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className={styles.uploadContainer}>
        <h6 className={styles.uploadTitle}>Upload CSV</h6>
        <form onSubmit={handleSubmit}>
          <div className={styles.fileInputWrapper}>
            <input
              id="upload-input"
              type="file"
              accept=".csv,text/csv"
              className={styles.fileInput}
              onChange={handleFileChange}
              disabled={disabled}
            />
          </div>
          <div className={styles.uploadButtonContainer}>
            <button type="submit" className={styles.uploadButton} disabled={loading || disabled}>
              {loading ? 'Uploading…' : 'Upload CSV'}
            </button>
          </div>
        </form>
      </div>
      <DataPreviewWidget data={uploadedData} loading={loading} />
    </>
  );
}
