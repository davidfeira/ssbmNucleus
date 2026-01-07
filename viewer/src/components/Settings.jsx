import { useState, useEffect } from 'react'
import './Settings.css'
import BackupRestore from './settings/BackupRestore'

const API_URL = 'http://127.0.0.1:5000/api/mex'

export default function Settings({ metadata }) {
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [message, setMessage] = useState({ text: '', type: '' }) // type: 'success' | 'error'

  // HD CSP generation state
  const [generatingHdCsps, setGeneratingHdCsps] = useState(false)
  const [hdCspProgress, setHdCspProgress] = useState({ current: 0, total: 0 })
  const [hdCspMessage, setHdCspMessage] = useState({ text: '', type: '' })
  const [hdCspResolution, setHdCspResolution] = useState('4x') // '2x' | '4x' | '8x' | '16x'

  // Vanilla ISO path state
  const [vanillaIsoPath, setVanillaIsoPath] = useState('')
  const [isoMessage, setIsoMessage] = useState({ text: '', type: '' })
  const [isoVerified, setIsoVerified] = useState(null) // null = not checked, true = valid, false = invalid
  const [verifyingIso, setVerifyingIso] = useState(false)

  // Slippi Dolphin path state
  const [slippiDolphinPath, setSlippiDolphinPath] = useState('')
  const [slippiMessage, setSlippiMessage] = useState({ text: '', type: '' })
  const [slippiVerified, setSlippiVerified] = useState(null)
  const [verifyingSlippi, setVerifyingSlippi] = useState(false)

  // Load vanilla ISO path from localStorage on mount and verify it
  useEffect(() => {
    const savedPath = localStorage.getItem('vanilla_iso_path')
    if (savedPath) {
      setVanillaIsoPath(savedPath)
      // Verify on load
      verifyIso(savedPath)
    }
  }, [])

  // Load Slippi Dolphin path from localStorage on mount and verify it
  useEffect(() => {
    const savedPath = localStorage.getItem('slippi_dolphin_path')
    if (savedPath) {
      setSlippiDolphinPath(savedPath)
      // Verify on load
      verifySlippiPath(savedPath)
    }
  }, [])

  const verifyIso = async (isoPath) => {
    setVerifyingIso(true)
    setIsoVerified(null)

    try {
      const response = await fetch(`${API_URL}/verify-iso`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isoPath })
      })

      const data = await response.json()

      if (data.success) {
        setIsoVerified(data.valid)
        if (!data.valid) {
          setIsoMessage({
            text: `Invalid ISO (MD5: ${data.md5.substring(0, 8)}...). Need vanilla Melee 1.02`,
            type: 'error'
          })
        }
      } else {
        setIsoVerified(false)
        setIsoMessage({ text: data.error, type: 'error' })
      }
    } catch (err) {
      setIsoVerified(false)
      setIsoMessage({ text: `Verification failed: ${err.message}`, type: 'error' })
    } finally {
      setVerifyingIso(false)
    }
  }

  const handleBrowseIso = async () => {
    if (!window.electron) {
      setIsoMessage({ text: 'Electron API not available', type: 'error' })
      return
    }

    try {
      const isoPath = await window.electron.openIsoDialog()
      if (isoPath) {
        setVanillaIsoPath(isoPath)
        setIsoMessage({ text: 'Verifying ISO...', type: '' })

        // Verify the ISO
        setVerifyingIso(true)
        const response = await fetch(`${API_URL}/verify-iso`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ isoPath })
        })

        const data = await response.json()

        if (data.success && data.valid) {
          localStorage.setItem('vanilla_iso_path', isoPath)
          setIsoVerified(true)
          setIsoMessage({ text: 'Valid vanilla Melee 1.02 ISO!', type: 'success' })
          setTimeout(() => setIsoMessage({ text: '', type: '' }), 3000)
        } else {
          setIsoVerified(false)
          setIsoMessage({
            text: `Invalid ISO. This is not a vanilla Melee 1.02 ISO.`,
            type: 'error'
          })
          // Don't save invalid ISO
          setVanillaIsoPath('')
        }
        setVerifyingIso(false)
      }
    } catch (err) {
      setIsoMessage({ text: `Error: ${err.message}`, type: 'error' })
      setVerifyingIso(false)
    }
  }

  const handleClearIsoPath = () => {
    localStorage.removeItem('vanilla_iso_path')
    setVanillaIsoPath('')
    setIsoVerified(null)
    setIsoMessage({ text: 'Vanilla ISO path cleared', type: 'success' })
    setTimeout(() => setIsoMessage({ text: '', type: '' }), 3000)
  }

  const verifySlippiPath = async (slippiPath) => {
    setVerifyingSlippi(true)
    setSlippiVerified(null)

    try {
      const response = await fetch(`${API_URL}/settings/slippi-path/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slippiPath })
      })

      const data = await response.json()

      if (data.success) {
        setSlippiVerified(data.valid)
        if (!data.valid) {
          setSlippiMessage({
            text: data.error || 'Invalid Slippi Dolphin path',
            type: 'error'
          })
        }
      } else {
        setSlippiVerified(false)
        setSlippiMessage({ text: data.error, type: 'error' })
      }
    } catch (err) {
      setSlippiVerified(false)
      setSlippiMessage({ text: `Verification failed: ${err.message}`, type: 'error' })
    } finally {
      setVerifyingSlippi(false)
    }
  }

  const handleBrowseSlippi = async () => {
    if (!window.electron) {
      setSlippiMessage({ text: 'Electron API not available', type: 'error' })
      return
    }

    try {
      const selectedPath = await window.electron.selectDirectory()
      if (selectedPath) {
        setSlippiDolphinPath(selectedPath)
        setSlippiMessage({ text: 'Verifying path...', type: '' })

        // Verify the path
        setVerifyingSlippi(true)
        const response = await fetch(`${API_URL}/settings/slippi-path/verify`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slippiPath: selectedPath })
        })

        const data = await response.json()

        if (data.success && data.valid) {
          localStorage.setItem('slippi_dolphin_path', selectedPath)
          setSlippiVerified(true)
          setSlippiMessage({ text: 'Valid Slippi Dolphin path!', type: 'success' })
          setTimeout(() => setSlippiMessage({ text: '', type: '' }), 3000)
        } else {
          setSlippiVerified(false)
          setSlippiMessage({
            text: data.error || 'Invalid path. Please select the Slippi netplay folder.',
            type: 'error'
          })
          // Don't save invalid path
          setSlippiDolphinPath('')
        }
        setVerifyingSlippi(false)
      }
    } catch (err) {
      setSlippiMessage({ text: `Error: ${err.message}`, type: 'error' })
      setVerifyingSlippi(false)
    }
  }

  const handleClearSlippiPath = () => {
    localStorage.removeItem('slippi_dolphin_path')
    setSlippiDolphinPath('')
    setSlippiVerified(null)
    setSlippiMessage({ text: 'Slippi Dolphin path cleared', type: 'success' })
    setTimeout(() => setSlippiMessage({ text: '', type: '' }), 3000)
  }

  // Calculate storage statistics
  const getStorageStats = () => {
    if (!metadata) return { characterCount: 0, stageCount: 0, costumeCount: 0 }

    const characterCount = Object.keys(metadata.characters || {}).length
    let costumeCount = 0

    Object.values(metadata.characters || {}).forEach(char => {
      costumeCount += (char.skins || []).length
    })

    let stageCount = 0
    Object.values(metadata.stages || {}).forEach(stage => {
      stageCount += (stage.variants || []).length
    })

    return { characterCount, stageCount, costumeCount }
  }

  const stats = getStorageStats()

  // Count skins missing HD CSPs
  const getHdCspStats = () => {
    if (!metadata?.characters) return { missing: 0, total: 0 }

    let missing = 0
    let total = 0

    Object.values(metadata.characters).forEach(char => {
      (char.skins || []).forEach(skin => {
        if (skin.has_csp) {
          total++
          if (!skin.has_hd_csp) {
            missing++
          }
        }
      })
    })

    return { missing, total }
  }

  const hdCspStats = getHdCspStats()

  const handleGenerateAllHdCsps = async () => {
    if (!metadata?.characters) return

    // Collect all skins that need HD CSPs
    const skinsToProcess = []
    Object.entries(metadata.characters).forEach(([charName, char]) => {
      (char.skins || []).forEach(skin => {
        if (skin.has_csp && !skin.has_hd_csp) {
          skinsToProcess.push({ character: charName, skinId: skin.id, color: skin.color })
        }
      })
    })

    if (skinsToProcess.length === 0) {
      setHdCspMessage({ text: 'All skins already have HD CSPs!', type: 'success' })
      setTimeout(() => setHdCspMessage({ text: '', type: '' }), 3000)
      return
    }

    setGeneratingHdCsps(true)
    setHdCspProgress({ current: 0, total: skinsToProcess.length })
    setHdCspMessage({ text: 'Generating HD CSPs...', type: '' })

    let successCount = 0
    let failCount = 0

    const scaleNum = parseInt(hdCspResolution.replace('x', ''))

    for (let i = 0; i < skinsToProcess.length; i++) {
      const skin = skinsToProcess[i]
      setHdCspProgress({ current: i + 1, total: skinsToProcess.length })

      try {
        const response = await fetch(
          `${API_URL}/storage/costumes/${encodeURIComponent(skin.character)}/${encodeURIComponent(skin.skinId)}/csp/capture-hd`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scale: scaleNum })
          }
        )
        const data = await response.json()
        if (data.success) {
          successCount++
        } else {
          console.error(`Failed to generate HD CSP for ${skin.character}/${skin.skinId}: ${data.error}`)
          failCount++
        }
      } catch (err) {
        console.error(`Error generating HD CSP for ${skin.character}/${skin.skinId}:`, err)
        failCount++
      }
    }

    setGeneratingHdCsps(false)
    setHdCspProgress({ current: 0, total: 0 })

    if (failCount === 0) {
      setHdCspMessage({ text: `Generated ${successCount} HD CSPs successfully!`, type: 'success' })
    } else {
      setHdCspMessage({ text: `Generated ${successCount} HD CSPs, ${failCount} failed`, type: 'error' })
    }

    setTimeout(() => setHdCspMessage({ text: '', type: '' }), 5000)
  }

  const handleClearStorage = () => {
    setShowConfirmModal(true)
  }

  const confirmClear = async () => {
    setShowConfirmModal(false)
    setClearing(true)
    setMessage({ text: 'Clearing storage...', type: '' })

    try {
      const response = await fetch(`${API_URL}/storage/clear`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      })

      const data = await response.json()

      if (data.success) {
        setMessage({ text: 'Storage cleared successfully!', type: 'success' })
        // Reload page after 1.5 seconds to refresh metadata
        setTimeout(() => {
          window.location.reload()
        }, 1500)
      } else {
        setMessage({ text: `Failed to clear storage: ${data.error}`, type: 'error' })
        setClearing(false)
      }
    } catch (err) {
      setMessage({ text: `Error: ${err.message}`, type: 'error' })
      setClearing(false)
    }
  }

  const cancelClear = () => {
    setShowConfirmModal(false)
  }


  return (
    <div className="settings-container">
      <div className="settings-content">
        <h2>Settings</h2>

        {/* Vanilla ISO Path */}
        <section className="settings-section">
          <h3>Vanilla ISO</h3>
          <p className="section-description">
            Set the path to your vanilla Melee ISO. This is required for applying xdelta patches.
          </p>

          <div className="iso-path-container">
            {vanillaIsoPath ? (
              <div className={`iso-path-display ${isoVerified === true ? 'verified' : isoVerified === false ? 'invalid' : ''}`}>
                <span className="iso-status-icon">
                  {verifyingIso ? '...' : isoVerified === true ? '✓' : isoVerified === false ? '✕' : '?'}
                </span>
                <span className="iso-path-text" title={vanillaIsoPath}>{vanillaIsoPath}</span>
                <button
                  className="iso-clear-button"
                  onClick={handleClearIsoPath}
                  title="Clear ISO path"
                >
                  ×
                </button>
              </div>
            ) : (
              <div className="iso-path-empty">No ISO path set</div>
            )}
            <button
              className="iso-browse-button"
              onClick={handleBrowseIso}
              disabled={verifyingIso}
            >
              {verifyingIso ? 'Verifying...' : vanillaIsoPath ? 'Change' : 'Browse'}
            </button>
          </div>

          {isoMessage.text && (
            <div className={`message ${isoMessage.type}`}>
              {isoMessage.text}
            </div>
          )}
        </section>

        {/* Slippi Dolphin Path */}
        <section className="settings-section">
          <h3>Slippi Dolphin</h3>
          <p className="section-description">
            Set the path to your Slippi Dolphin netplay folder for texture pack generation.
            <br />
            <span className="path-hint">Example: C:\Users\[you]\AppData\Roaming\Slippi Launcher\netplay</span>
          </p>

          <div className="iso-path-container">
            {slippiDolphinPath ? (
              <div className={`iso-path-display ${slippiVerified === true ? 'verified' : slippiVerified === false ? 'invalid' : ''}`}>
                <span className="iso-status-icon">
                  {verifyingSlippi ? '...' : slippiVerified === true ? '✓' : slippiVerified === false ? '✕' : '?'}
                </span>
                <span className="iso-path-text" title={slippiDolphinPath}>{slippiDolphinPath}</span>
                <button
                  className="iso-clear-button"
                  onClick={handleClearSlippiPath}
                  title="Clear Slippi path"
                >
                  ×
                </button>
              </div>
            ) : (
              <div className="iso-path-empty">No Slippi Dolphin path set</div>
            )}
            <button
              className="iso-browse-button"
              onClick={handleBrowseSlippi}
              disabled={verifyingSlippi}
            >
              {verifyingSlippi ? 'Verifying...' : slippiDolphinPath ? 'Change' : 'Browse'}
            </button>
          </div>

          {slippiVerified && slippiDolphinPath && (
            <div className="derived-paths">
              <div className="derived-path">
                <span className="derived-label">Dump:</span>
                <span className="derived-value">{slippiDolphinPath}/User/Dump/Textures/GALE01</span>
              </div>
              <div className="derived-path">
                <span className="derived-label">Load:</span>
                <span className="derived-value">{slippiDolphinPath}/User/Load/Textures/GALE01</span>
              </div>
            </div>
          )}

          {slippiMessage.text && (
            <div className={`message ${slippiMessage.type}`}>
              {slippiMessage.text}
            </div>
          )}
        </section>

        {/* Storage Statistics */}
        <section className="settings-section">
          <h3>Storage Statistics</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">{stats.costumeCount}</div>
              <div className="stat-label">Costumes</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{stats.stageCount}</div>
              <div className="stat-label">Stage Variants</div>
            </div>
          </div>
        </section>

        {/* Vault Backup & Restore Section */}
        <BackupRestore API_URL={API_URL} />

        {/* HD CSP Generation Section */}
        <section className="settings-section">
          <h3>HD Portrait Generation</h3>
          <p className="section-description">
            Generate high-resolution CSPs for texture pack mode where memory constraints don't apply.
          </p>

          <div className="hd-csp-tool">
            <div className="hd-csp-tool-info">
              <div className="hd-csp-stats">
                <span className="stat-highlight">{hdCspStats.missing}</span> skins missing HD CSPs
                <span className="stat-muted"> / {hdCspStats.total} total</span>
              </div>
            </div>

            <div className="hd-csp-controls">
              <div className="hd-csp-resolution-select">
                <label>Resolution</label>
                <div className="hd-csp-resolution-options">
                  {['2x', '4x', '8x', '16x'].map(res => (
                    <button
                      key={res}
                      className={`hd-csp-resolution-btn ${hdCspResolution === res ? 'active' : ''}`}
                      onClick={() => setHdCspResolution(res)}
                      disabled={generatingHdCsps}
                    >
                      {res}
                    </button>
                  ))}
                </div>
              </div>

              <button
                className="hd-csp-generate-btn"
                onClick={handleGenerateAllHdCsps}
                disabled={generatingHdCsps || hdCspStats.missing === 0}
              >
                {generatingHdCsps ? (
                  <>
                    <span className="spinner"></span>
                    {hdCspProgress.current} / {hdCspProgress.total}
                  </>
                ) : hdCspStats.missing === 0 ? (
                  'All Done'
                ) : (
                  'Generate All'
                )}
              </button>
            </div>
          </div>

          {hdCspMessage.text && (
            <div className={`message ${hdCspMessage.type}`}>
              {hdCspMessage.text}
            </div>
          )}
        </section>

        {/* Clear Storage Section */}
        <section className="settings-section">
          <h3>Clear Storage</h3>
          <p className="section-description">
            Remove all character costumes and stage variants from storage. This action cannot be undone.
          </p>

          <button
            className="clear-button"
            onClick={handleClearStorage}
            disabled={clearing}
          >
            {clearing ? 'Clearing...' : 'Clear Storage'}
          </button>

          {message.text && (
            <div className={`message ${message.type}`}>
              {message.text}
            </div>
          )}
        </section>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="modal-overlay" onClick={cancelClear}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Confirm Clear Storage</h3>
            <p>
              Are you sure you want to clear all storage? This will remove:
            </p>
            <ul>
              <li>All character costumes ({stats.costumeCount} items)</li>
              <li>All stage variants ({stats.stageCount} items)</li>
              <li>Storage metadata</li>
            </ul>
            <p className="warning-text">
              This action cannot be undone!
            </p>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={cancelClear}>
                Cancel
              </button>
              <button className="btn-confirm" onClick={confirmClear}>
                Clear Storage
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
