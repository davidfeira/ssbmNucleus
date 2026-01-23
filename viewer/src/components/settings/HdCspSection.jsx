/**
 * HdCspSection - HD CSP generation functionality
 *
 * Features:
 * - Calculate missing HD CSPs
 * - Generate HD CSPs at 2x, 3x, or 4x resolution
 * - Progress tracking during batch generation
 * - Success/error messaging
 */
import { useState } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'

export default function HdCspSection({ metadata, API_URL }) {
  const [generatingHdCsps, setGeneratingHdCsps] = useState(false)
  const [hdCspProgress, setHdCspProgress] = useState({ current: 0, total: 0 })
  const [hdCspMessage, setHdCspMessage] = useState({ text: '', type: '' })
  const [hdCspResolution, setHdCspResolution] = useState('2x') // '2x' | '3x' | '4x'

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

  return (
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
              {['2x', '3x', '4x'].map(res => (
                <button
                  key={res}
                  className={`hd-csp-resolution-btn ${hdCspResolution === res ? 'active' : ''}`}
                  onMouseEnter={playHoverSound}
                  onClick={() => { playSound('tick'); setHdCspResolution(res); }}
                  disabled={generatingHdCsps}
                >
                  {res}
                </button>
              ))}
            </div>
          </div>

          <button
            className="hd-csp-generate-btn"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); handleGenerateAllHdCsps(); }}
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
  )
}
