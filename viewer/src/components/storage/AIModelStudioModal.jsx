import { useEffect, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { API_URL, BACKEND_URL } from '../../config'
import { playSound } from '../../utils/sounds'
import ProgressPanel from '../export/ProgressPanel'

/**
 * AI Model Studio: the 3D-model sibling of the AI Skin Studio. Describe a
 * character (or upload a .glb/.obj mesh), the lab generates the model, rigs
 * it onto this character's skeleton, and imports it as a playable costume.
 */
export default function AIModelStudioModal({ show, character, onClose, onSaved }) {
  const [status, setStatus] = useState(null)
  const [phase, setPhase] = useState('form')   // form | running | preview | saving
  const [theme, setTheme] = useState('')
  const [meshFile, setMeshFile] = useState(null)     // data URL
  const [meshName, setMeshName] = useState('')
  const [preview, setPreview] = useState(null)
  const [skinName, setSkinName] = useState('')
  const [error, setError] = useState(null)
  const [labStatus, setLabStatus] = useState(null)   // /model-lab/status payload
  const socketRef = useRef(null)

  const cleanupSocket = () => {
    if (socketRef.current) {
      socketRef.current.disconnect()
      socketRef.current = null
    }
  }

  useEffect(() => {
    if (!show) {
      cleanupSocket()
      setPhase('form')
      setStatus(null)
      setPreview(null)
      setError(null)
      return cleanupSocket
    }
    fetch(`${API_URL}/model-lab/status`)
      .then((r) => r.json())
      .then(setLabStatus)
      .catch(() => setLabStatus({ enabled: false }))
    return cleanupSocket
  }, [show])

  if (!show) return null

  const pickMesh = (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    const reader = new FileReader()
    reader.onload = () => {
      setMeshFile(reader.result)
      setMeshName(f.name)
    }
    reader.readAsDataURL(f)
  }

  const run = async () => {
    if (!theme.trim() && !meshFile) return
    playSound('start')
    setPhase('running')
    setError(null)
    setStatus({ percentage: null, message: 'Starting…' })

    cleanupSocket()
    const socket = io(BACKEND_URL)
    socketRef.current = socket
    socket.on('modellab_progress', (d) => setStatus((prev) => ({
      ...prev,
      ...d,
      percentage: Number.isFinite(d.percentage) ? d.percentage : prev?.percentage,
    })))
    socket.on('modellab_complete', (d) => {
      setPreview(d.preview)
      setSkinName(theme.trim() || meshName.replace(/\.[^.]+$/, ''))
      setPhase('preview')
      playSound('achievement')
      cleanupSocket()
    })
    socket.on('modellab_error', (d) => {
      setError(d.error || 'Model Studio failed')
      setPhase('form')
      playSound('error')
      cleanupSocket()
    })

    try {
      const res = await fetch(`${API_URL}/model-lab/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character,
          theme: theme.trim() || undefined,
          meshFile: meshFile || undefined,
          meshName: meshName || undefined,
        }),
      })
      const data = await res.json()
      if (!data.success) {
        setError(data.error || 'Could not start the Model Studio')
        setPhase('form')
        cleanupSocket()
      }
    } catch (err) {
      setError(`Could not start: ${err.message}`)
      setPhase('form')
      cleanupSocket()
    }
  }

  const save = async () => {
    setPhase('saving')
    try {
      const res = await fetch(`${API_URL}/model-lab/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: skinName.trim() || 'AI Model' }),
      })
      const data = await res.json()
      if (!data.success) throw new Error(data.error || 'save failed')
      playSound('achievement')
      onSaved?.()
      onClose()
    } catch (err) {
      setError(`Save failed: ${err.message}`)
      setPhase('preview')
      playSound('error')
    }
  }

  const discard = async () => {
    await fetch(`${API_URL}/model-lab/discard`, { method: 'POST' }).catch(() => {})
    setPhase('form')
    setPreview(null)
    setMeshFile(null)
    setMeshName('')
  }

  const handleClose = () => {
    if (phase === 'running') return
    if (phase === 'preview') discard()
    onClose()
  }

  const canGenerate = Boolean(labStatus?.canGenerate)

  return (
    <div className="ai-studio-overlay" onClick={handleClose}>
      <div className="ai-studio-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ai-studio-header">
          <h3>🧊 AI Model Studio — {character}</h3>
          <button className="ai-studio-close" onClick={handleClose}>×</button>
        </div>

        {phase === 'form' && (
          <div className="ai-studio-form">
            <label className="ai-studio-label">
              {canGenerate
                ? 'Describe the character model you want'
                : 'Local 3D generation is unavailable — upload a mesh instead'}
            </label>
            <textarea
              className="ai-studio-theme"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              placeholder={canGenerate
                ? 'e.g. "a chunky robot knight with a round helmet" — generated in a T-pose and rigged onto the skeleton'
                : 'optional notes (the mesh upload below is used)'}
              rows={3}
              autoFocus
              disabled={!canGenerate && !meshFile}
            />
            <label className="ai-studio-label">…or use an existing 3D model (.glb / .obj)</label>
            <input type="file" accept=".glb,.gltf,.obj,.smd" onChange={pickMesh} />
            {meshName && <div className="ai-studio-step">{meshName}</div>}
            <p className="ai-studio-label" style={{ opacity: 0.7 }}>
              The model is decimated to Melee scale, rigged onto {character}&apos;s
              skeleton with surface weight transfer, and imported as a costume.
              Eye-blink animations are not carried over.
            </p>
            {error && <div className="ai-studio-error">{error}</div>}
            <div className="ai-studio-actions">
              <button className="ai-studio-btn primary"
                      disabled={!theme.trim() && !meshFile}
                      onClick={run}>
                {meshFile ? 'Rig & Import' : 'Generate'}
              </button>
              <button className="ai-studio-btn" onClick={handleClose}>Cancel</button>
            </div>
          </div>
        )}

        {phase === 'running' && (
          <ProgressPanel
            title="Building your model…"
            label="Model Studio progress"
            progressValue={Number.isFinite(status?.percentage) ? status.percentage : null}
            metaText={Number.isFinite(status?.percentage) ? `${Math.round(status.percentage)}%` : null}
            messageText={status?.message || 'Starting…'}
          />
        )}

        {(phase === 'preview' || phase === 'saving') && (
          <div className="ai-studio-preview">
            {preview
              ? <img className="ai-studio-sheet" src={preview} alt="model preview" />
              : <div className="ai-studio-step">no preview render available</div>}
            <label className="ai-studio-label">Skin name</label>
            <input className="ai-studio-theme" value={skinName}
                   onChange={(e) => setSkinName(e.target.value)} />
            {error && <div className="ai-studio-error">{error}</div>}
            <div className="ai-studio-actions">
              <button className="ai-studio-btn primary" disabled={phase === 'saving'}
                      onClick={save}>
                {phase === 'saving' ? 'Saving…' : 'Save to vault'}
              </button>
              <button className="ai-studio-btn" disabled={phase === 'saving'}
                      onClick={discard}>
                Discard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
