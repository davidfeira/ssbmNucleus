/**
 * IsoPathSection - Vanilla ISO path management
 *
 * Features:
 * - Browse for vanilla Melee ISO
 * - Verify ISO against MD5 hash
 * - Display verification status
 * - Persist path to localStorage
 */
import { useState, useEffect } from 'react'

export default function IsoPathSection({ API_URL }) {
  const [vanillaIsoPath, setVanillaIsoPath] = useState('')
  const [isoMessage, setIsoMessage] = useState({ text: '', type: '' })
  const [isoVerified, setIsoVerified] = useState(null) // null = not checked, true = valid, false = invalid
  const [verifyingIso, setVerifyingIso] = useState(false)

  // Load vanilla ISO path from localStorage on mount and verify it
  useEffect(() => {
    const savedPath = localStorage.getItem('vanilla_iso_path')
    if (savedPath) {
      setVanillaIsoPath(savedPath)
      // Verify on load
      verifyIso(savedPath)
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

  return (
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
  )
}
