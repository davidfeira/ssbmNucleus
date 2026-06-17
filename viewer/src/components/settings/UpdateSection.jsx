/**
 * UpdateSection - Check for and install app updates from releases.ssbmnucleus.net
 */
import { useState, useEffect, useRef } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'

export default function UpdateSection() {
  const [currentVersion, setCurrentVersion] = useState('')
  const [checking, setChecking] = useState(false)
  const [update, setUpdate] = useState(null)
  const [upToDate, setUpToDate] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const cleanupRef = useRef(null)

  const isElectron = Boolean(window.electron?.checkForUpdate)

  useEffect(() => {
    if (window.electron?.getAppVersion) {
      window.electron.getAppVersion().then(setCurrentVersion).catch(() => {})
    }
    return () => {
      if (cleanupRef.current) cleanupRef.current()
    }
  }, [])

  const handleCheck = async () => {
    setChecking(true)
    setError(null)
    setUpToDate(false)
    try {
      const result = await window.electron.checkForUpdate()
      if (!result.success) {
        setError(result.error || 'Update check failed')
      } else if (result.update) {
        setUpdate(result.update)
      } else {
        setUpdate(null)
        setUpToDate(true)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setChecking(false)
    }
  }

  const handleInstall = async () => {
    setDownloading(true)
    setError(null)
    setProgress(0)
    cleanupRef.current = window.electron.onUpdateProgress(({ received, total }) => {
      setProgress(total > 0 ? Math.round((received / total) * 100) : 0)
    })
    try {
      const result = await window.electron.installUpdate()
      if (!result.success) {
        setError(result.error || 'Update failed')
        setDownloading(false)
      }
      // On success the installer launches and the app quits on its own.
    } catch (err) {
      setError(err.message)
      setDownloading(false)
    } finally {
      if (cleanupRef.current) {
        cleanupRef.current()
        cleanupRef.current = null
      }
    }
  }

  if (!isElectron) {
    return null
  }

  return (
    <section className="settings-section">
      <h3>Updates</h3>
      <p className="section-description">
        Current version: <strong>{currentVersion ? `v${currentVersion}` : '...'}</strong>
      </p>

      {update ? (
        <div className="update-available">
          <div className="update-shine-badge" aria-hidden="true">
            <span />
          </div>
          <div className="update-available-copy">
            <p className="update-available-kicker">Update detected</p>
            <p className="update-available-version">v{update.version} is available</p>
          </div>
          {update.notes && <p className="update-notes">{update.notes}</p>}
          <button
            className="restore-button update-install-button"
            disabled={downloading}
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('start'); handleInstall(); }}
          >
            {downloading ? `Downloading... ${progress}%` : `Update to v${update.version}`}
          </button>
          {downloading && (
            <div className="update-progress-track">
              <div className="update-progress-fill" style={{ width: `${progress}%` }} />
            </div>
          )}
          <p className="setup-section-note">
            The installer will open after the download finishes and the app will close.
          </p>
        </div>
      ) : (
        <button
          className="restore-button"
          disabled={checking}
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); handleCheck(); }}
        >
          {checking ? 'Checking...' : 'Check for Updates'}
        </button>
      )}

      {upToDate && !update && (
        <p className="update-status-ok">You&apos;re up to date.</p>
      )}
      {error && (
        <p className="update-status-error">Update failed: {error}</p>
      )}
    </section>
  )
}
