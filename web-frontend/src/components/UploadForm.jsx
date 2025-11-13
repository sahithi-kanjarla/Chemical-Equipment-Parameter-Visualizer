// src/components/UploadForm.jsx
import React, { useState } from 'react';
import api from '../api';

export default function UploadForm({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

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
      });

      // IMPORTANT: call onUploaded with the whole response data (includes preview_rows)
      if (onUploaded) onUploaded(res.data);

      // Optionally show a success message
      alert('Upload successful — summary loaded.');
      setFile(null);
      // reset file input (if you want, remove any selected file UI)
      // document.getElementById('upload-input').value = '';
    } catch (err) {
      console.error('Upload failed', err);
      const msg = err?.response?.data?.detail || err?.message || 'Upload failed';
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-3 mb-3">
      <h6>Upload CSV</h6>
      <form onSubmit={handleSubmit}>
        <div className="mb-2">
          <input
            id="upload-input"
            type="file"
            accept=".csv,text/csv"
            className="form-control form-control-sm"
            onChange={handleFileChange}
          />
        </div>
        <div className="d-grid gap-2">
          <button type="submit" className="btn btn-primary btn-sm" disabled={loading}>
            {loading ? 'Uploading…' : 'Upload CSV'}
          </button>
        </div>
      </form>
    </div>
  );
}
