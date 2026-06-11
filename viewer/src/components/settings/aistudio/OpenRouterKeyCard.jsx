/**
 * OpenRouterKeyCard - the OpenRouter API key (extracted from the old
 * AiStudioSection). Stored in localStorage and sent with studio requests;
 * the backend's own OPENROUTER_API_KEY env is the fallback.
 */
import { useState } from 'react'
import { playHoverSound, playSound } from '../../../utils/sounds'

export default function OpenRouterKeyCard({ backendHasKey, onChanged }) {
  const [key, setKey] = useState(localStorage.getItem('openrouter_api_key') || '')
  const [revealed, setRevealed] = useState(false)
  const [message, setMessage] = useState('')

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
    onChanged?.()
  }

  return (
    <div className="aistudio-card">
      <div className="aistudio-card-title">OpenRouter API key</div>
      <p className="section-description">
        Plans the skins and powers the API image models.
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
            ? 'Backend already has a key — set one here to override'
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
