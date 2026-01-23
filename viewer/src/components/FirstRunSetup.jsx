import { useState, useEffect } from 'react'
import { io } from 'socket.io-client'
import { playSound } from '../utils/sounds'
import './FirstRunSetup.css'

const API_URL = 'http://127.0.0.1:5000/api/mex'

export default function FirstRunSetup({ onComplete }) {
  const [step, setStep] = useState('welcome') // welcome, select-iso, verifying, extracting, copying, complete, error
  const [isoPath, setIsoPath] = useState('')
  const [progress, setProgress] = useState({
    phase: '',
    percentage: 0,
    message: '',
    completed: 0,
    total: 0
  })
  const [error, setError] = useState(null)
  const [socket, setSocket] = useState(null)

  // Connect to WebSocket for progress updates
  useEffect(() => {
    const newSocket = io('http://127.0.0.1:5000', {
      transports: ['websocket', 'polling']
    })

    newSocket.on('connect', () => {
      console.log('[FirstRunSetup] WebSocket connected')
    })

    newSocket.on('setup_progress', (data) => {
      console.log('[FirstRunSetup] Progress:', data)
      setProgress(data)

      // Update step based on phase
      if (data.phase === 'extracting') {
        setStep('extracting')
      } else if (data.phase === 'copying_characters' || data.phase === 'copying_stages' || data.phase === 'copying_csp_data' || data.phase === 'extracting_sounds') {
        setStep('copying')
      } else if (data.phase === 'complete') {
        setStep('complete')
      }
    })

    newSocket.on('setup_complete', (data) => {
      console.log('[FirstRunSetup] Complete:', data)
      setStep('complete')
      setProgress({
        phase: 'complete',
        percentage: 100,
        message: `Setup complete! Extracted ${data.characters} characters and ${data.stages} stages.`,
        completed: 100,
        total: 100
      })
      // Save the ISO path to localStorage so Settings page can find it
      if (data.isoPath) {
        localStorage.setItem('vanilla_iso_path', data.isoPath)
      }
    })

    newSocket.on('setup_error', (data) => {
      console.log('[FirstRunSetup] Error:', data)
      playSound('error')
      setStep('error')
      setError(data.error)
    })

    setSocket(newSocket)

    return () => {
      newSocket.disconnect()
    }
  }, [])

  const handleBrowseIso = async () => {
    if (!window.electron) {
      playSound('error')
      setError('Electron API not available')
      return
    }

    try {
      const selectedPath = await window.electron.openIsoDialog()
      if (selectedPath) {
        setIsoPath(selectedPath)
      }
    } catch (err) {
      playSound('error')
      setError(`Error selecting file: ${err.message}`)
    }
  }

  const handleStartSetup = async () => {
    if (!isoPath) {
      playSound('error')
      setError('Please select an ISO file')
      return
    }

    playSound('start')
    setStep('verifying')
    setError(null)

    try {
      // Start the setup process (backend will verify and extract)
      const response = await fetch(`${API_URL}/setup/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isoPath })
      })

      const data = await response.json()

      if (!data.success) {
        playSound('error')
        setStep('error')
        setError(data.error || 'Setup failed')
        return
      }

      // Setup started, progress will come via WebSocket
      setStep('extracting')

    } catch (err) {
      playSound('error')
      setStep('error')
      setError(`Failed to start setup: ${err.message}`)
    }
  }

  const handleComplete = () => {
    onComplete()
  }

  const handleRetry = () => {
    setStep('welcome')
    setIsoPath('')
    setError(null)
    setProgress({
      phase: '',
      percentage: 0,
      message: '',
      completed: 0,
      total: 0
    })
  }

  // Render different steps
  const renderWelcome = () => (
    <div className="setup-step">
      <div className="setup-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
      </div>
      <h2>Welcome to SSBM Nucleus</h2>
      <p className="setup-description">
        Before you can use Nucleus, we need to set up the vanilla Melee assets.
        This is required for legal reasons - we can't distribute copyrighted game files.
      </p>
      <p className="setup-description">
        You'll need to provide your own <strong>vanilla Super Smash Bros. Melee 1.02 (NTSC) ISO</strong>.
        This is typically named <code>GALE01</code>.
      </p>
      <div className="setup-note">
        <strong>Note:</strong> Only the original, unmodified Melee 1.02 ISO will work.
        Modified or other region ISOs won't be accepted.
      </div>
      <button className="btn-primary" onClick={() => setStep('select-iso')}>
        Get Started
      </button>
    </div>
  )

  const renderSelectIso = () => (
    <div className="setup-step">
      <h2>Select Your Melee ISO</h2>
      <p className="setup-description">
        Browse to your vanilla Melee 1.02 (NTSC) ISO file.
      </p>

      <div className="iso-selector">
        <input
          type="text"
          value={isoPath}
          placeholder="No file selected..."
          readOnly
          className="iso-path-input"
        />
        <button className="btn-secondary" onClick={handleBrowseIso}>
          Browse...
        </button>
      </div>

      {error && (
        <div className="setup-error">
          {error}
        </div>
      )}

      <div className="setup-buttons">
        <button className="btn-secondary" onClick={() => setStep('welcome')}>
          Back
        </button>
        <button
          className="btn-primary"
          onClick={handleStartSetup}
          disabled={!isoPath}
        >
          Start Setup
        </button>
      </div>
    </div>
  )

  const renderVerifying = () => (
    <div className="setup-step">
      <div className="setup-spinner"></div>
      <h2>Verifying ISO</h2>
      <p className="setup-description">
        Checking that this is a valid vanilla Melee 1.02 ISO...
      </p>
    </div>
  )

  const renderExtracting = () => (
    <div className="setup-step">
      <h2>Extracting ISO</h2>
      <p className="setup-description">
        {progress.message || 'Extracting game files... This may take 1-2 minutes.'}
      </p>
      <div className="progress-container">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress.percentage}%` }}
          ></div>
        </div>
        <div className="progress-text">{progress.percentage}%</div>
      </div>
    </div>
  )

  const renderCopying = () => (
    <div className="setup-step">
      <h2>Copying Assets</h2>
      <p className="setup-description">
        {progress.message || 'Copying character and stage assets...'}
      </p>
      <div className="progress-container">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress.percentage}%` }}
          ></div>
        </div>
        <div className="progress-text">
          {progress.completed} / {progress.total}
        </div>
      </div>
    </div>
  )

  const renderComplete = () => (
    <div className="setup-step">
      <div className="setup-icon success">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
      </div>
      <h2>Setup Complete!</h2>
      <p className="setup-description">
        {progress.message || 'All vanilla assets have been extracted. You can now use SSBM Nucleus!'}
      </p>
      <button className="btn-primary" onClick={handleComplete}>
        Get Started
      </button>
    </div>
  )

  const renderError = () => (
    <div className="setup-step">
      <div className="setup-icon error">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
      </div>
      <h2>Setup Failed</h2>
      <p className="setup-description error-text">
        {error || 'An unknown error occurred during setup.'}
      </p>
      <div className="setup-buttons">
        <button className="btn-primary" onClick={handleRetry}>
          Try Again
        </button>
      </div>
    </div>
  )

  return (
    <div className="first-run-overlay">
      <div className="first-run-modal">
        <div className="first-run-header">
          <img src="/nucleuslogo.png" alt="SSBM Nucleus" className="first-run-logo" />
          <h1>First-Time Setup</h1>
        </div>

        <div className="first-run-content">
          {step === 'welcome' && renderWelcome()}
          {step === 'select-iso' && renderSelectIso()}
          {step === 'verifying' && renderVerifying()}
          {step === 'extracting' && renderExtracting()}
          {step === 'copying' && renderCopying()}
          {step === 'complete' && renderComplete()}
          {step === 'error' && renderError()}
        </div>

        <div className="first-run-footer">
          <div className="step-indicator">
            <div className={`step-dot ${['welcome', 'select-iso', 'verifying', 'extracting', 'copying', 'complete'].indexOf(step) >= 0 ? 'active' : ''}`}></div>
            <div className={`step-dot ${['select-iso', 'verifying', 'extracting', 'copying', 'complete'].indexOf(step) >= 0 ? 'active' : ''}`}></div>
            <div className={`step-dot ${['verifying', 'extracting', 'copying', 'complete'].indexOf(step) >= 0 ? 'active' : ''}`}></div>
            <div className={`step-dot ${['extracting', 'copying', 'complete'].indexOf(step) >= 0 ? 'active' : ''}`}></div>
            <div className={`step-dot ${['copying', 'complete'].indexOf(step) >= 0 ? 'active' : ''}`}></div>
            <div className={`step-dot ${step === 'complete' ? 'active' : ''}`}></div>
          </div>
        </div>
      </div>
    </div>
  )
}
