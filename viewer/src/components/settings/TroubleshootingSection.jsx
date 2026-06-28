/**
 * TroubleshootingSection - one-click logs export for bug reports.
 *
 * Bundles the app's log files into a zip the user can attach when reporting an
 * issue, so we get real debug info instead of a vague description. The Discord
 * itself is linked in its own Settings section (Community).
 */
import { useState } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'

export default function TroubleshootingSection({ API_URL }) {
  const [creating, setCreating] = useState(false)
  const [message, setMessage] = useState({ text: '', type: '' })

  const handleCreateLogsZip = async () => {
    setCreating(true)
    setMessage({ text: 'Creating logs zip...', type: '' })
    try {
      // Include the user's Slippi Dolphin logs/crash dumps too (if we know the
      // path) so a crash playing a Nucleus-built ISO in Slippi is debuggable.
      const slippiPath = localStorage.getItem('slippi_dolphin_path') || ''
      const qs = slippiPath ? `?slippiPath=${encodeURIComponent(slippiPath)}` : ''
      // Fetch as a blob so we can confirm success and trigger a named download
      // (works the same in Electron and the browser).
      const response = await fetch(`${API_URL}/logs/download${qs}`)
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`)
      }
      const blob = await response.blob()
      const disposition = response.headers.get('Content-Disposition') || ''
      const match = disposition.match(/filename="?([^"]+)"?/)
      const filename = match ? match[1] : 'nucleus-logs.zip'

      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      playSound('start')
      setMessage({ text: 'Logs zip saved — share it with the team when asked.', type: 'success' })
      setTimeout(() => setMessage({ text: '', type: '' }), 6000)
    } catch (err) {
      setMessage({ text: `Could not create logs zip: ${err.message}`, type: 'error' })
    } finally {
      setCreating(false)
    }
  }

  return (
    <section className="settings-section">
      <h3>Troubleshooting</h3>
      <p className="section-description">
        Hit a bug or crash? Report it in the <strong>#bug-reports</strong> channel
        on our Discord (linked above) and describe what went wrong. A maintainer
        may ask for your logs — if so, use the button below to create a zip and
        share it with them.
      </p>
      <p className="section-description section-note">
        Heads up: the logs zip includes your file paths and Slippi Dolphin logs,
        so only share it with the team when asked — don't post it publicly.
      </p>

      <button
        className="backup-button"
        onMouseEnter={playHoverSound}
        onClick={() => { playSound('start'); handleCreateLogsZip(); }}
        disabled={creating}
      >
        {creating ? 'Creating Logs Zip...' : 'Create Logs Zip'}
      </button>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}
    </section>
  )
}
