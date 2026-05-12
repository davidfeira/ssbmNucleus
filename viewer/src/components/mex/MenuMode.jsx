/**
 * MenuMode - Menus tab of the MexPanel (installation UI).
 *
 * Mirrors the character extras pattern:
 * - Sidebar starts with CSS / SSS (like character list)
 * - Click CSS → sidebar becomes submod types (Icon Grid, Doors, Background)
 * - Click a submod type → right panel shows "Currently in MEX" + "Available to Import"
 */
import { useState, useEffect, useCallback } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL, BACKEND_URL } from '../../config'

const MENU_TYPES = [
  { key: 'css', name: 'Character Select Screen', short: 'CSS' },
  { key: 'sss', name: 'Stage Select Screen', short: 'SSS' },
]

const CSS_SUBMOD_TYPES = [
  { key: 'icon_grid', name: 'Icon Grid', description: 'Character portraits on the CSS banner' },
  { key: 'doors', name: 'Doors', description: 'Character panel door animations' },
  { key: 'background', name: 'Background', description: 'CSS background and stage art' },
]

export default function MenuMode({ mode, onModeChange }) {
  const [selectedMenu, setSelectedMenu] = useState(null)
  const [selectedSubmod, setSelectedSubmod] = useState(null)
  const [selectedMod, setSelectedMod] = useState(null)
  const [iconGridMods, setIconGridMods] = useState([])
  const [loading, setLoading] = useState(false)
  const [installing, setInstalling] = useState(false)
  const [installMessage, setInstallMessage] = useState('')
  const [installedMods, setInstalledMods] = useState({}) // submod_key -> mod

  const fetchIconGridMods = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/menus/css/icon_grid/list`)
      const data = await res.json()
      if (data.success) setIconGridMods(data.mods || [])
    } catch (err) {
      console.error('Failed to fetch icon grid mods:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (selectedMenu === 'css') fetchIconGridMods()
  }, [selectedMenu, fetchIconGridMods])

  const getModsForSubmod = (key) => {
    if (key === 'icon_grid') return iconGridMods
    return [] // doors, background not wired yet
  }

  const handleInstall = async () => {
    if (!selectedMod) return
    setInstalling(true)
    setInstallMessage('')
    try {
      const res = await fetch(`${API_URL}/menus/css/icon_grid/install/${selectedMod.id}`, {
        method: 'POST'
      })
      const data = await res.json()
      if (data.success) {
        playSound('newSkin')
        setInstallMessage(`✓ ${data.message}`)
        setInstalledMods(prev => ({ ...prev, [selectedSubmod]: selectedMod }))
      } else {
        playSound('error')
        setInstallMessage(`✗ ${data.error}`)
      }
    } catch (err) {
      playSound('error')
      setInstallMessage(`✗ ${err.message}`)
    } finally {
      setInstalling(false)
      setTimeout(() => setInstallMessage(''), 4000)
    }
  }

  const submodTypes = selectedMenu === 'css' ? CSS_SUBMOD_TYPES : []

  // ── Submod type selected → extras-style view ──
  if (selectedMenu && selectedSubmod) {
    const submod = submodTypes.find(s => s.key === selectedSubmod)
    const mods = getModsForSubmod(selectedSubmod)

    return (
      <div className="mex-content">
        {/* Left sidebar: submod types list (like extras list) */}
        <div className="fighters-list">
          <div className="extras-header">
            <h3>{selectedMenu.toUpperCase()} Mods</h3>
            <button
              className="btn-back-small"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('back'); setSelectedSubmod(null); setSelectedMod(null) }}
            >
              ← Back
            </button>
          </div>
          <div className="fighter-items">
            {submodTypes.map(st => (
              <div
                key={st.key}
                className={`fighter-item ${selectedSubmod === st.key ? 'selected' : ''}`}
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); setSelectedSubmod(st.key); setSelectedMod(null) }}
              >
                <div className="fighter-content">
                  <div className="fighter-name">{st.name}</div>
                  <div className="fighter-info">
                    <span className="costume-count">
                      {getModsForSubmod(st.key).length} in vault
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel: Currently in MEX + Available to Import */}
        <div className="costumes-panel">
          {/* Currently in MEX */}
          <div className="costumes-section">
            <h3>Currently in MEX</h3>
            <div className="costume-list existing">
              {installedMods[selectedSubmod] ? (
                <div className="costume-card existing-costume">
                  <div className="costume-preview">
                    {installedMods[selectedSubmod].screenshotUrl ? (
                      <img
                        src={`${BACKEND_URL}${installedMods[selectedSubmod].screenshotUrl}`}
                        alt={installedMods[selectedSubmod].name}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', color: 'var(--color-text-muted, #888)', fontSize: '0.8rem' }}>
                        {installedMods[selectedSubmod].name?.[0] || '?'}
                      </div>
                    )}
                  </div>
                  <div className="costume-info">
                    <h4>{installedMods[selectedSubmod].name}</h4>
                    <span style={{ fontSize: '11px', color: '#888' }}>{installedMods[selectedSubmod].icon_count || 0} icons</span>
                  </div>
                </div>
              ) : (
                <div className="costume-card existing-costume vanilla-extra">
                  <div className="costume-preview" style={{ padding: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', color: 'var(--color-text-muted, #888)', fontSize: '0.8rem' }}>
                      Vanilla
                    </div>
                  </div>
                  <div className="costume-info">
                    <h4>Vanilla</h4>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Available to Import */}
          <div className="costumes-section">
            <div className="costumes-section-header">
              <h3>Available to Import</h3>
              <div className="batch-controls">
                {selectedMod && (
                  <button
                    className="btn-batch-import"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('start'); handleInstall() }}
                    disabled={installing}
                  >
                    {installing ? 'Installing...' : 'Import Selected'}
                  </button>
                )}
                {installMessage && (
                  <span style={{ fontSize: '0.8rem', color: installMessage.startsWith('✓') ? 'var(--color-success, #4caf50)' : 'var(--color-error, #f44336)' }}>
                    {installMessage}
                  </span>
                )}
              </div>
            </div>
            <div className="costume-list">
              {loading ? (
                <div className="no-costumes"><p>Loading...</p></div>
              ) : mods.length === 0 ? (
                <div className="no-costumes">
                  <p>No {submod?.name || 'mods'} in vault. Import some from the Menus vault tab first.</p>
                </div>
              ) : (
                mods.map(mod => (
                  <div
                    key={mod.id}
                    className={`costume-card ${selectedMod?.id === mod.id ? 'selected' : ''}`}
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('boop'); setSelectedMod(mod) }}
                  >
                    <div className="costume-preview">
                      {mod.screenshotUrl ? (
                        <img
                          src={`${BACKEND_URL}${mod.screenshotUrl}`}
                          alt={mod.name}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onError={(e) => { e.target.style.display = 'none' }}
                        />
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', color: 'var(--color-text-muted, #888)' }}>
                          {mod.name?.[0] || '?'}
                        </div>
                      )}
                      <input
                        type="checkbox"
                        className="costume-checkbox"
                        checked={selectedMod?.id === mod.id}
                        readOnly
                      />
                    </div>
                    <div className="costume-info">
                      <h4>{mod.name}</h4>
                      <span style={{ fontSize: '11px', color: '#888' }}>{mod.icon_count || 0} icons</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── Menu type selected → show submod types in sidebar ──
  if (selectedMenu) {
    return (
      <div className="mex-content">
        <div className="fighters-list">
          <div className="extras-header">
            <h3>{selectedMenu.toUpperCase()} Mods</h3>
            <button
              className="btn-back-small"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('back'); setSelectedMenu(null) }}
            >
              ← Back
            </button>
          </div>
          <div className="fighter-items">
            {submodTypes.map(st => (
              <div
                key={st.key}
                className={`fighter-item`}
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); setSelectedSubmod(st.key) }}
              >
                <div className="fighter-content">
                  <div className="fighter-name">{st.name}</div>
                  <div className="fighter-info">
                    <span className="costume-count">{getModsForSubmod(st.key).length} in vault</span>
                  </div>
                </div>
              </div>
            ))}
            {selectedMenu === 'sss' && (
              <div style={{ padding: '1rem', color: 'var(--color-text-muted, #888)', fontSize: '0.8rem', textAlign: 'center' }}>
                SSS mod types coming soon
              </div>
            )}
          </div>
        </div>

        <div className="costumes-panel">
          <div className="no-selection">
            <p>Select a mod type from the sidebar</p>
          </div>
        </div>
      </div>
    )
  }

  // ── Default: menu type selection (CSS / SSS) ──
  return (
    <div className="mex-content">
      <div className="fighters-list">
        <div className="fighters-header">
          <div className="mode-toggle">
            <button
              className={`mode-toggle-btn ${mode === 'characters' ? 'active' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={() => { if (mode !== 'characters') { playSound('boop'); onModeChange('characters') } }}
            >
              Fighters
            </button>
            <button
              className={`mode-toggle-btn ${mode === 'stages' ? 'active' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={() => { if (mode !== 'stages') { playSound('boop'); onModeChange('stages') } }}
            >
              Stages
            </button>
            <button
              className={`mode-toggle-btn ${mode === 'menus' ? 'active' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={() => { if (mode !== 'menus') { playSound('boop'); onModeChange('menus') } }}
            >
              Menus
            </button>
          </div>
          <span className="fighters-count">{MENU_TYPES.length}</span>
        </div>

        <div className="fighter-items">
          {MENU_TYPES.map(mt => (
            <div
              key={mt.key}
              className="fighter-item"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('boop'); setSelectedMenu(mt.key) }}
            >
              <div className="fighter-content">
                <div className="fighter-name">{mt.short}</div>
                <div className="fighter-info">
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted, #888)' }}>{mt.name}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="costumes-panel">
        <div className="no-selection">
          <p>Select a menu type from the sidebar</p>
        </div>
      </div>
    </div>
  )
}
