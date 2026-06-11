/**
 * AiStudioSection - OpenRouter API key for the AI Skin/Stage Studios
 *
 * The key is stored in localStorage and sent with each studio request; the
 * backend falls back to its own OPENROUTER_API_KEY env when unset. Only
 * rendered when the backend reports the AI lab enabled.
 */
import { useState, useEffect } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'

export default function AiStudioSection({ API_URL }) {
  const [enabled, setEnabled] = useState(false)
  const [backendHasKey, setBackendHasKey] = useState(false)
  const [key, setKey] = useState(localStorage.getItem('openrouter_api_key') || '')
  const [revealed, setRevealed] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetch(`${API_URL}/skin-lab/ai-status`)
      .then((r) => r.json())
      .then((d) => {
        setEnabled(Boolean(d.enabled))
        setBackendHasKey(Boolean(d.hasKey))
      })
      .catch(() => setEnabled(false))
  }, [API_URL])

  if (!enabled) return null

  const save = () => {
    const trimmed = key.trim()
    if (trimmed) {
      localStorage.setItem('openrouter_api_key', trimmed)
      setMessage('Key saved')
    } else {
      localStorage.removeItem('openrouter_api_key')
      setMessage('Key cleared')
    }
    playSound('boop')
    setTimeout(() => setMessage(''), 3000)
  }

  return (
    <section className="settings-section">
      <h3>AI Studio</h3>
      <p className="section-description">
        OpenRouter API key for the AI Skin / Stage Studios (plans the skins and,
        optionally, generates materials).
        <br />
        <span className="path-hint">
          Get one at openrouter.ai/keys — a skin costs well under a cent to plan;
          API image generation adds ~3¢ per material (local image models are free).
        </span>
      </p>
      <div className="iso-path-container">
        <input
          className="ai-studio-name"
          style={{ flex: 1 }}
          type={revealed ? 'text' : 'password'}
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder={backendHasKey
            ? 'Backend already has a key — set one here to override'
            : 'sk-or-v1-…'}
        />
        <button
          className="iso-browse-button"
          onMouseEnter={playHoverSound}
          onClick={() => setRevealed(!revealed)}
        >
          {revealed ? 'Hide' : 'Show'}
        </button>
        <button
          className="iso-browse-button"
          onMouseEnter={playHoverSound}
          onClick={save}
        >
          Save
        </button>
      </div>
      {message && <div className="message success">{message}</div>}
    </section>
  )
}
