import React, { useState, useEffect } from 'react';
import './MexPanel.css';
import IsoBuilder from './IsoBuilder';

const MexPanel = () => {
  const [mexStatus, setMexStatus] = useState(null);
  const [fighters, setFighters] = useState([]);
  const [selectedFighter, setSelectedFighter] = useState(null);
  const [storageCostumes, setStorageCostumes] = useState([]);
  const [mexCostumes, setMexCostumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importingCostume, setImportingCostume] = useState(null); // Track which costume is being imported
  const [showIsoBuilder, setShowIsoBuilder] = useState(false);

  const API_URL = 'http://127.0.0.1:5000/api/mex';

  useEffect(() => {
    fetchMexStatus();
    fetchFighters();
    fetchStorageCostumes();
  }, []);

  useEffect(() => {
    if (selectedFighter) {
      fetchMexCostumes(selectedFighter.name);
    }
  }, [selectedFighter]);

  const fetchMexStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/status`);
      const data = await response.json();
      setMexStatus(data);
    } catch (err) {
      setError('Failed to connect to MEX API');
      console.error(err);
    }
  };

  const fetchFighters = async () => {
    try {
      const response = await fetch(`${API_URL}/fighters`);
      const data = await response.json();
      if (data.success) {
        setFighters(data.fighters);
      }
    } catch (err) {
      console.error('Failed to fetch fighters:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStorageCostumes = async () => {
    try {
      const response = await fetch(`${API_URL}/storage/costumes`);
      const data = await response.json();
      if (data.success) {
        setStorageCostumes(data.costumes);
      }
    } catch (err) {
      console.error('Failed to fetch storage costumes:', err);
    }
  };

  const fetchMexCostumes = async (fighterName) => {
    try {
      const response = await fetch(`${API_URL}/fighters/${encodeURIComponent(fighterName)}/costumes`);
      const data = await response.json();
      if (data.success) {
        setMexCostumes(data.costumes || []);
      }
    } catch (err) {
      console.error('Failed to fetch MEX costumes:', err);
      setMexCostumes([]);
    }
  };

  const handleImportCostume = async (costume) => {
    // Prevent multiple simultaneous imports
    if (importing || importingCostume) {
      console.log('Import already in progress, ignoring click');
      return;
    }

    console.log(`=== IMPORT REQUEST ===`);
    console.log(`Costume:`, costume);
    console.log(`Fighter: ${costume.character}`);
    console.log(`Zip Path: ${costume.zipPath}`);

    setImporting(true);
    setImportingCostume(costume.zipPath);

    try {
      const requestBody = {
        fighter: costume.character,
        costumePath: costume.zipPath
      };

      console.log('Sending import request:', requestBody);

      const response = await fetch(`${API_URL}/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();
      console.log('Import response:', data);

      if (data.success) {
        alert(`Successfully imported costume to ${costume.character}!\n${data.result.costumesImported} costume(s) added.`);
        // Refresh fighters and MEX costumes to show updated data
        fetchFighters();
        if (selectedFighter) {
          fetchMexCostumes(selectedFighter.name);
        }
      } else {
        alert(`Import failed: ${data.error}`);
      }
    } catch (err) {
      console.error('Import error:', err);
      alert(`Import error: ${err.message}`);
    } finally {
      setImporting(false);
      setImportingCostume(null);
    }
  };

  const getCostumesForFighter = (fighterName) => {
    return storageCostumes.filter(c => c.character === fighterName);
  };

  if (loading) {
    return <div className="mex-panel loading">Loading MEX Manager...</div>;
  }

  if (error) {
    return (
      <div className="mex-panel error">
        <h2>MEX Connection Error</h2>
        <p>{error}</p>
        <p>Make sure the backend is running:</p>
        <code>python backend/mex_api.py</code>
      </div>
    );
  }

  return (
    <div className="mex-panel">
      <div className="mex-header">
        <h2>MEX Manager</h2>
        {mexStatus?.connected && (
          <div className="mex-status connected">
            <span className="status-dot"></span>
            <span>{mexStatus.project.name} v{mexStatus.project.version}</span>
          </div>
        )}
      </div>

      <div className="mex-actions">
        <button
          className="btn-primary"
          onClick={() => setShowIsoBuilder(true)}
        >
          Export ISO
        </button>
        <button
          className="btn-secondary"
          onClick={fetchFighters}
        >
          Refresh
        </button>
      </div>

      {mexStatus?.counts && (
        <div className="mex-stats">
          <div className="stat">
            <span className="stat-value">{mexStatus.counts.fighters}</span>
            <span className="stat-label">Fighters</span>
          </div>
          <div className="stat">
            <span className="stat-value">{mexStatus.counts.stages}</span>
            <span className="stat-label">Stages</span>
          </div>
          <div className="stat">
            <span className="stat-value">{mexStatus.counts.music}</span>
            <span className="stat-label">Music</span>
          </div>
        </div>
      )}

      <div className="mex-content">
        <div className="fighters-list">
          <h3>Fighters ({fighters.length})</h3>
          <div className="fighter-items">
            {fighters.map(fighter => {
              const availableCostumes = getCostumesForFighter(fighter.name);
              return (
                <div
                  key={fighter.internalId}
                  className={`fighter-item ${selectedFighter?.internalId === fighter.internalId ? 'selected' : ''}`}
                  onClick={() => setSelectedFighter(fighter)}
                >
                  <div className="fighter-name">{fighter.name}</div>
                  <div className="fighter-info">
                    <span className="costume-count">{fighter.costumeCount} in MEX</span>
                    {availableCostumes.length > 0 && (
                      <span className="available-count">{availableCostumes.length} available</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="costumes-panel">
          {selectedFighter ? (
            <>
              <div className="costumes-section">
                <h3>Already in MEX ({mexCostumes.length})</h3>
                <div className="costume-list existing">
                  {mexCostumes.map((costume, idx) => (
                    <div key={idx} className="costume-card existing-costume">
                      {costume.cspUrl && (
                        <div className="costume-preview">
                          <img
                            src={`${API_URL}${costume.cspUrl}`}
                            alt={costume.name}
                            onError={(e) => e.target.style.display = 'none'}
                          />
                        </div>
                      )}
                      <div className="costume-info">
                        <h4>{costume.name}</h4>
                        <p className="costume-file">{costume.fileName}</p>
                        <div className="costume-assets">
                          {costume.iconUrl && (
                            <div className="stock-icon">
                              <img
                                src={`${API_URL}${costume.iconUrl}`}
                                alt="Stock"
                                onError={(e) => e.target.style.display = 'none'}
                              />
                            </div>
                          )}
                          <div className="costume-badges">
                            {costume.hasCSP && <span className="badge">CSP</span>}
                            {costume.hasIcon && <span className="badge">Stock</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  {mexCostumes.length === 0 && (
                    <div className="no-costumes">
                      <p>No costumes in MEX yet</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="costumes-section">
                <h3>Available to Import</h3>
                <div className="costume-list">
                  {getCostumesForFighter(selectedFighter.name).map((costume, idx) => (
                    <div key={idx} className="costume-card">
                      <div className="costume-preview">
                        {costume.cspUrl && (
                          <img
                            src={costume.cspUrl}
                            alt={costume.name}
                            onError={(e) => e.target.style.display = 'none'}
                          />
                        )}
                      </div>
                      <div className="costume-info">
                        <h4>{costume.name}</h4>
                        <p className="costume-code">{costume.costumeCode}</p>
                        <div className="costume-assets">
                          {costume.stockUrl && (
                            <div className="stock-icon">
                              <img
                                src={costume.stockUrl}
                                alt="Stock"
                                onError={(e) => e.target.style.display = 'none'}
                              />
                            </div>
                          )}
                        </div>
                        <button
                          className="btn-add"
                          onClick={() => handleImportCostume(costume)}
                          disabled={importing}
                        >
                          {importingCostume === costume.zipPath ? 'Importing...' : importing ? 'Wait...' : 'Add to MEX'}
                        </button>
                      </div>
                    </div>
                  ))}
                  {getCostumesForFighter(selectedFighter.name).length === 0 && (
                    <div className="no-costumes">
                      <p>No costumes available in storage for {selectedFighter.name}</p>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="no-selection">
              <p>Select a fighter to view costumes</p>
            </div>
          )}
        </div>
      </div>

      {showIsoBuilder && (
        <IsoBuilder onClose={() => setShowIsoBuilder(false)} />
      )}
    </div>
  );
};

export default MexPanel;
