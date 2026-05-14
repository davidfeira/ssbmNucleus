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
import SssLayoutEditor from '../storage/SssLayoutEditor'
import CssLayoutEditor from '../storage/CssLayoutEditor'
import HexagonLoader from '../shared/HexagonLoader'

const MENU_TYPES = [
  { key: 'css', name: 'Character Select Screen', short: 'CSS' },
  { key: 'sss', name: 'Stage Select Screen', short: 'SSS' },
]

const CSS_SUBMOD_TYPES = [
  { key: 'icon_grid', name: 'Icon Grid', description: 'Character portraits on the CSS banner' },
  { key: 'doors', name: 'Doors', description: 'Character panel door animations' },
  { key: 'background', name: 'Background', description: 'CSS background and stage art' },
]

const SSS_SUBMOD_TYPES = [
  { key: 'background', name: 'Background', description: 'SSS background model and animations' },
]

export default function MenuMode({ mode, onModeChange }) {
  const [selectedMenu, setSelectedMenu] = useState(null)
  const [selectedSubmod, setSelectedSubmod] = useState(null)
  const [selectedMod, setSelectedMod] = useState(null)
  const [iconGridMods, setIconGridMods] = useState([])
  const [bgMods, setBgMods] = useState([])
  const [doorMods, setDoorMods] = useState([])
  const [loading, setLoading] = useState(false)
  const [installing, setInstalling] = useState(false)
  const [installMessage, setInstallMessage] = useState('')
  const [installProgress, setInstallProgress] = useState(null) // { current, total, character }
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

  const fetchBgMods = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/menus/background/list`)
      const data = await res.json()
      if (data.success) setBgMods(data.mods || [])
    } catch (err) {
      console.error('Failed to fetch background mods:', err)
    }
  }, [])

  const fetchDoorMods = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/menus/css/doors/list`)
      const data = await res.json()
      if (data.success) setDoorMods(data.mods || [])
    } catch (err) {
      console.error('Failed to fetch door mods:', err)
    }
  }, [])

  useEffect(() => {
    if (selectedMenu === 'css') {
      fetchIconGridMods()
      fetchBgMods()
      fetchDoorMods()
    }
    if (selectedMenu === 'sss') {
      fetchBgMods()
    }
  }, [selectedMenu, fetchIconGridMods, fetchBgMods, fetchDoorMods])

  const getModsForSubmod = (key) => {
    if (key === 'icon_grid') return iconGridMods
    if (key === 'background') return bgMods
    if (key === 'doors') return doorMods
    return []
  }

  const handleInstall = async () => {
    if (!selectedMod) return
    setInstalling(true)
    setInstallMessage('')
    setInstallProgress(null)
    try {
      if (selectedSubmod === 'icon_grid') {
        // Per-icon install with progress
        const planRes = await fetch(`${API_URL}/menus/css/icon_grid/install/${selectedMod.id}`, { method: 'POST' })
        const plan = await planRes.json()
        if (!plan.success) { playSound('error'); setInstallMessage(`✗ ${plan.error}`); return }

        const icons = plan.icons
        let installed = 0, errors = []
        for (let i = 0; i < icons.length; i++) {
          setInstallProgress({ current: i + 1, total: icons.length, character: icons[i].character })
          try {
            const res = await fetch(`${API_URL}/menus/css/icon_grid/install/${selectedMod.id}/icon`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(icons[i])
            })
            const data = await res.json()
            if (data.success) installed++
            else errors.push(icons[i].character)
          } catch { errors.push(icons[i].character) }
        }

        if (installed > 0) {
          playSound('newSkin')
          let msg = `✓ Installed ${installed} icon(s). Rebuild ISO to apply.`
          if (errors.length) msg += ` (${errors.length} failed)`
          setInstallMessage(msg)
          setInstalledMods(prev => ({ ...prev, [selectedSubmod]: selectedMod }))
        } else {
          playSound('error')
          setInstallMessage(`✗ No icons installed`)
        }
      } else {
        let installEndpoint
        if (selectedMenu === 'sss' && selectedSubmod === 'background') {
          installEndpoint = `${API_URL}/menus/sss/background/install/${selectedMod.id}`
        } else if (selectedSubmod === 'background') {
          installEndpoint = `${API_URL}/menus/css/background/install/${selectedMod.id}`
        } else if (selectedSubmod === 'doors') {
          installEndpoint = `${API_URL}/menus/css/doors/install/${selectedMod.id}`
        } else {
          installEndpoint = `${API_URL}/menus/css/icon_grid/install/${selectedMod.id}`
        }
        const res = await fetch(installEndpoint, { method: 'POST' })
        const data = await res.json()
        if (data.success) {
          playSound('newSkin')
          setInstallMessage(`✓ ${data.message}`)
          setInstalledMods(prev => ({ ...prev, [selectedSubmod]: selectedMod }))
        } else {
          playSound('error')
          setInstallMessage(`✗ ${data.error}`)
        }
      }
    } catch (err) {
      playSound('error')
      setInstallMessage(`✗ ${err.message}`)
    } finally {
      setInstalling(false)
      setInstallProgress(null)
      setTimeout(() => setInstallMessage(''), 4000)
    }
  }

  const submodTypes = selectedMenu === 'css' ? CSS_SUBMOD_TYPES
    : selectedMenu === 'sss' ? SSS_SUBMOD_TYPES : []

  // ── Layout editors (not a normal import flow) ──
  if ((selectedMenu === 'css' || selectedMenu === 'sss') && selectedSubmod === 'layout') {
    const EditorComponent = selectedMenu === 'css' ? CssLayoutEditor : SssLayoutEditor
    const menuLabel = selectedMenu.toUpperCase()
    return (
      <div className="mex-content">
        <div className="fighters-list">
          <div className="extras-header">
            <h3>{menuLabel} Mods</h3>
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
                      {st.key === 'layout' ? 'editor' : `${getModsForSubmod(st.key).length} in vault`}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="costumes-panel" style={{ overflow: 'hidden', flexDirection: 'column' }}>
          <EditorComponent />
        </div>
      </div>
    )
  }

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
                      {st.key === 'layout' ? 'editor' : `${getModsForSubmod(st.key).length} in vault`}
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
                      {(mod.screenshotUrl || mod.imageUrl) ? (
                        <img
                          src={`${BACKEND_URL}${mod.screenshotUrl || mod.imageUrl}`}
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

        {installing && (
          <div className="import-overlay">
            <div className="import-modal import-modal--hexagon">
              <HexagonLoader
                className="import-loader"
                size={104}
                label="Installing mod"
                progress={installProgress ? (installProgress.current / installProgress.total) * 100 : null}
                minimumVisibleProgress={6}
              />
              <h3>Installing...</h3>
              <p className="import-status">
                {installProgress
                  ? `${installProgress.character} (${installProgress.current}/${installProgress.total})`
                  : 'Please wait...'}
              </p>
            </div>
          </div>
        )}
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
                    <span className="costume-count">{st.key === 'layout' ? 'editor' : `${getModsForSubmod(st.key).length} in vault`}</span>
                  </div>
                </div>
              </div>
            ))}
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
              <div className="fighter-content" style={{ flex: 1 }}>
                <div className="fighter-name">{mt.short}</div>
                <div className="fighter-info">
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted, #888)' }}>{mt.name}</span>
                </div>
              </div>
              <button
                className="sss-action-btn add"
                style={{ flex: 'none', padding: '0.4rem 0.75rem', fontSize: '0.75rem' }}
                onMouseEnter={playHoverSound}
                onClick={(e) => {
                  e.stopPropagation()
                  playSound('boop')
                  setSelectedMenu(mt.key)
                  setSelectedSubmod('layout')
                }}
              >
                Edit Layout
              </button>
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
