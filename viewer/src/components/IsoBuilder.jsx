import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import './IsoBuilder.css';

const IsoBuilder = ({ onClose }) => {
  const [filename, setFilename] = useState(`game_${new Date().toISOString().slice(0, 10)}.iso`);
  const [cspCompression, setCspCompression] = useState(1.0);
  const [exporting, setExporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState(null);
  const [socket, setSocket] = useState(null);

  const API_URL = 'http://127.0.0.1:5000';

  useEffect(() => {
    // Connect to WebSocket for progress updates
    const newSocket = io(API_URL);

    newSocket.on('connect', () => {
      console.log('Connected to WebSocket');
    });

    newSocket.on('export_progress', (data) => {
      setProgress(data.percentage);
      setMessage(data.message || `Exporting... ${data.percentage}%`);
    });

    newSocket.on('export_complete', (data) => {
      setProgress(100);
      setMessage('Export complete!');
      setComplete(true);
      setExporting(false);
    });

    newSocket.on('export_error', (data) => {
      setError(data.error);
      setExporting(false);
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, []);

  const handleStartExport = async () => {
    setExporting(true);
    setProgress(0);
    setMessage('Starting export...');
    setError(null);
    setComplete(false);

    try {
      const response = await fetch(`${API_URL}/api/mex/export/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename,
          cspCompression
        })
      });

      const data = await response.json();

      if (!data.success) {
        setError(data.error);
        setExporting(false);
      }
    } catch (err) {
      setError(`Failed to start export: ${err.message}`);
      setExporting(false);
    }
  };

  const handleDownload = () => {
    window.open(`${API_URL}/api/mex/export/download/${filename}`, '_blank');
  };

  return (
    <div className="iso-builder-overlay">
      <div className="iso-builder-modal">
        <div className="modal-header">
          <h2>Export ISO</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {!exporting && !complete && !error && (
            <>
              <div className="form-group">
                <label htmlFor="filename">Output Filename:</label>
                <input
                  type="text"
                  id="filename"
                  value={filename}
                  onChange={(e) => setFilename(e.target.value)}
                  placeholder="game.iso"
                />
              </div>

              <div className="form-group">
                <label htmlFor="compression">
                  CSP Compression
                </label>
                <div className="compression-input-group">
                  <input
                    type="number"
                    id="compression-input"
                    min="0.1"
                    max="1.0"
                    step="0.01"
                    value={cspCompression}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      if (!isNaN(val) && val >= 0.1 && val <= 1.0) {
                        setCspCompression(val);
                      }
                    }}
                    className="compression-number-input"
                  />
                  <span className="compression-multiplier">x</span>
                </div>
                <input
                  type="range"
                  id="compression"
                  min="0.1"
                  max="1.0"
                  step="0.01"
                  value={cspCompression}
                  onChange={(e) => setCspCompression(parseFloat(e.target.value))}
                  className="compression-slider"
                />
                <div className="compression-hints">
                  <span className="hint-label">0.1 (Tiny)</span>
                  <span className="hint-recommended">Recommended: 0.98</span>
                  <span className="hint-label">1.0 (Full)</span>
                </div>
                <p className="compression-info">
                  Lower values reduce CSP image size. Try 0.98 if CSPs appear corrupted.
                </p>
              </div>

              <div className="warning-box">
                <p><strong>Warning:</strong> ISO export may take 5-10 minutes.</p>
                <p>The browser will remain responsive. You can continue working while the export runs in the background.</p>
              </div>

              <button
                className="btn-export"
                onClick={handleStartExport}
              >
                Start Export
              </button>
            </>
          )}

          {exporting && (
            <div className="export-progress">
              <div className="progress-header">
                <h3>Exporting ISO...</h3>
                <span className="progress-percentage">{progress}%</span>
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>

              <p className="progress-message">{message}</p>

              <div className="export-spinner">
                <div className="spinner"></div>
              </div>
            </div>
          )}

          {complete && (
            <div className="export-complete">
              <div className="success-icon">✓</div>
              <h3>Export Complete!</h3>
              <p>Your modified ISO is ready to download.</p>
              <div className="complete-actions">
                <button className="btn-download" onClick={handleDownload}>
                  Download {filename}
                </button>
                <button className="btn-secondary" onClick={onClose}>
                  Close
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="export-error">
              <div className="error-icon">✕</div>
              <h3>Export Failed</h3>
              <p className="error-message">{error}</p>
              <button className="btn-secondary" onClick={onClose}>
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IsoBuilder;
