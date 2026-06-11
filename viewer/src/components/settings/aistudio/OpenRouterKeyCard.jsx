/**
 * OpenRouterKeyCard - the OpenRouter API key, stored ENCRYPTED at rest by
 * the backend (DPAPI on Windows) via POST /ai-engine/key. The key is
 * write-only from the UI: we show whether one is set, never the key itself.
 * A legacy plaintext-localStorage key is migrated automatically on mount.
 */
import { useEffect, useRef, useState } from 'react'
import { playHoverSound, playSound } from '../../../utils/sounds'

export default function OpenRouterKeyCard({ API_URL, backendHasKey, onChanged }) {
  const [key, setKey] = useState('')
  const [revealed, setRevealed] = useState(false)
  const [message, setMessage] = useState('')
  const migratedRef = useRef(false)

  const postKey = async (value) => {
    const res = await fetch(`${API_URL}/ai-engine/key`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: value }),
    })
    return res.json()
  }

  // one-time migration: a key from the old plaintext-localStorage scheme
  // moves into the encrypted backend store and is wiped from localStorage
  useEffect(() => {
    if (migratedRef.current) return
    migratedRef.current = true
    const legacy = localStorage.getItem('openrouter_api_key')
    if (!legacy) return
    postKey(legacy).then((d) => {
      if (d.success && d.hasKey) {
        localStorage.removeItem('openrouter_api_key')
        setMessage('Existing key moved to encrypted storage')
        setTimeout(() => setMessage(''), 4000)
        onChanged?.()
      }
    }).catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const save = async () => {
    const trimmed = key.trim()
    try {
      const d = await postKey(trimmed)
      if (!d.success) throw new Error(d.error || 'save failed')
      setMessage(trimmed ? 'Key saved (encrypted)' : 'Key cleared')
      setKey('')
      playSound('boop')
      onChanged?.()
    } catch (err) {
      setMessage(`Could not save: ${err.message}`)
      playSound('error')
    }
    setTimeout(() => setMessage(''), 3000)
  }

  return (
    <div className="aistudio-card">
      <div className="aistudio-card-title">
        OpenRouter API key
        {backendHasKey && <span className="aistudio-badge good">key set</span>}
      </div>
      <p className="section-description">
        Plans the skins and powers the API image models. Stored encrypted on
        this machine — never shown again after saving.
        <span className="path-hint">
          {' '}Get one at openrouter.ai/keys — planning a skin costs well under
          a cent; API image generation bills per material.
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
            ? 'A key is set — enter a new one to replace it, or save empty to clear'
            : 'sk-or-v1-…'}
        />
        <button className="iso-browse-button" onMouseEnter={playHoverSound}
                onClick={() => setRevealed(!revealed)}>
          {revealed ? 'Hide' : 'Show'}
        </button>
        <button className="iso-browse-button" onMouseEnter={playHoverSound}
                onClick={save}>
          Save
        </button>
      </div>
      {message && <div className="message success">{message}</div>}
    </div>
  )
}
