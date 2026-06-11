import { useState, useEffect, useCallback, useRef } from 'react'
import SssCanvas from './SssCanvas'
import CssIconProperties from './CssIconProperties'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL } from '../../config'

const CSS_BASE_WIDTH = 3.5
const CSS_BASE_HEIGHT = 3.4
const CSS_TEMPLATE_WIDTH = 35.05
const CSS_TEMPLATE_HEIGHT = 28.8

function applyCssTemplate(icons, template) {
  const { iconsPerRow, scaleX, scaleY, centerX, centerY, iconWidth, iconHeight,
          iconSideDropX, iconSideDropY, iconSideDropZ } = template
  const count = icons.length
  if (count === 0 || iconsPerRow <= 0) return icons

  const rows = Math.ceil(count / iconsPerRow)
  const iw = iconWidth * scaleX
  const ih = iconHeight * scaleY
  const totalW = Math.min(count, iconsPerRow) * iw
  const totalH = rows * ih

  return icons.map((icon, i) => {
    const col = i % iconsPerRow
    const row = Math.floor(i / iconsPerRow)
    const iconsInRow = row === rows - 1 ? count - row * iconsPerRow : iconsPerRow
    const isEdge = col === 0 || col === iconsInRow - 1

    let x = centerX - totalW / 2 + iw * col + iw / 2
    let y = centerY + totalH / 2 - ih * row - ih / 2
    let z = 0
    let colOffX = 0, colOffY = 0

    if (isEdge) {
      colOffX = -iconSideDropX
      colOffY = -iconSideDropY
      z = iconSideDropZ
    }

    return {
      ...icon,
      x, y, z,
      scaleX, scaleY,
      collisionSizeX: iconWidth,
      collisionSizeY: iconHeight,
      collisionOffsetX: colOffX,
      collisionOffsetY: colOffY
    }
  })
}

function getCssCollisionRect(icon) {
  return {
    ox: icon.collisionOffsetX || 0,
    oy: icon.collisionOffsetY || 0,
    w: (icon.collisionSizeX || 7.05) / 2 * icon.scaleX,
    h: (icon.collisionSizeY || 7.2) / 2 * icon.scaleY
  }
}

export default function CssLayoutEditor() {
  const [layout, setLayout] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [dirty, setDirty] = useState(false)
  const [selectedIndices, setSelectedIndices] = useState([])
  const [propsPopup, setPropsPopup] = useState(null)
  const [zoom, setZoom] = useState(8)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const [showCollision, setShowCollision] = useState(true)
  const [showOverscan, setShowOverscan] = useState(false)
  const [useTemplate, setUseTemplate] = useState(false)

  useEffect(() => { fetchLayout() }, [])

  const fetchLayout = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch(`${API_URL}/menus/css/layout`)
      const data = await resp.json()
      if (data.success) {
        setLayout(data)
        setSelectedIndices([])
        setDirty(false)
      } else {
        setError(data.error || 'Failed to load layout')
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!layout) return
    setSaving(true)
    try {
      const resp = await fetch(`${API_URL}/menus/css/layout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ icons: layout.icons, template: layout.template })
      })
      const data = await resp.json()
      if (data.success) {
        setDirty(false)
        await fetchLayout()
      } else {
        alert(`Save failed: ${data.error}`)
      }
    } catch (e) {
      alert(`Save error: ${e.message}`)
    } finally {
      setSaving(false)
    }
  }

  const icons = layout?.icons || []

  const updateIcons = useCallback((newIcons) => {
    setLayout(prev => prev ? { ...prev, icons: newIcons } : prev)
    setDirty(true)
  }, [])

  const updateTemplate = useCallback((newTemplate) => {
    setLayout(prev => prev ? { ...prev, template: newTemplate } : prev)
    setDirty(true)
  }, [])

  const maybeApplyTemplate = useCallback((icns) => {
    if (!useTemplate || !layout?.template) return icns
    return applyCssTemplate(icns, layout.template)
  }, [useTemplate, layout?.template])

  const handleToggleTemplate = useCallback((on) => {
    setUseTemplate(on)
    if (on && layout?.template) {
      updateIcons(applyCssTemplate(icons, layout.template))
    }
  }, [layout, icons, updateIcons])

  const primaryIdx = selectedIndices.length > 0 ? selectedIndices[0] : -1

  const handleSelectionChange = useCallback((indices) => setSelectedIndices(indices), [])

  const handleMoveIcon = useCallback((idx, dx, dy) => {
    const newIcons = [...icons]
    newIcons[idx] = { ...newIcons[idx], x: newIcons[idx].x + dx, y: newIcons[idx].y + dy }
    updateIcons(newIcons)
  }, [icons, updateIcons])

  const handleMoveIcons = useCallback((indices, dx, dy) => {
    const newIcons = [...icons]
    indices.forEach(idx => {
      newIcons[idx] = { ...newIcons[idx], x: newIcons[idx].x + dx, y: newIcons[idx].y + dy }
    })
    updateIcons(newIcons)
  }, [icons, updateIcons])

  const swapIcons = useCallback((arr, i, j) => {
    const a = arr[i], b = arr[j]
    arr[i] = { ...b, x: a.x, y: a.y, z: a.z, scaleX: a.scaleX, scaleY: a.scaleY,
               collisionSizeX: a.collisionSizeX, collisionSizeY: a.collisionSizeY,
               collisionOffsetX: a.collisionOffsetX, collisionOffsetY: a.collisionOffsetY }
    arr[j] = { ...a, x: b.x, y: b.y, z: b.z, scaleX: b.scaleX, scaleY: b.scaleY,
               collisionSizeX: b.collisionSizeX, collisionSizeY: b.collisionSizeY,
               collisionOffsetX: b.collisionOffsetX, collisionOffsetY: b.collisionOffsetY }
    return arr
  }, [])

  const handleSwapIcons = useCallback((i, j) => {
    const newIcons = [...icons]
    swapIcons(newIcons, i, j)
    updateIcons(maybeApplyTemplate(newIcons))
  }, [icons, updateIcons, maybeApplyTemplate, swapIcons])

  const handleUpdateIcon = useCallback((indices, updates) => {
    const newIcons = [...icons]
    const idxList = Array.isArray(indices) ? indices : [indices]
    idxList.forEach(idx => { newIcons[idx] = { ...newIcons[idx], ...updates } })
    updateIcons(newIcons)
  }, [icons, updateIcons])

  const handleAddIcon = useCallback(() => {
    const newIcon = {
      index: icons.length,
      x: 0, y: 0, z: 0,
      scaleX: 1, scaleY: 1,
      fighter: 0, fighterName: null,
      sfxID: 205,
      collisionOffsetX: 0, collisionOffsetY: 0,
      collisionSizeX: 7.05, collisionSizeY: 7.2,
      iconPath: null, status: 2
    }
    const newIcons = maybeApplyTemplate([...icons, newIcon])
    updateIcons(newIcons)
    setSelectedIndices([newIcons.length - 1])
  }, [icons, updateIcons, maybeApplyTemplate])

  const handleRemoveIcon = useCallback(() => {
    if (selectedIndices.length === 0) return
    const removeSet = new Set(selectedIndices)
    const newIcons = icons.filter((_, i) => !removeSet.has(i))
    updateIcons(maybeApplyTemplate(newIcons))
    setSelectedIndices([])
  }, [icons, selectedIndices, updateIcons, maybeApplyTemplate])

  const handleMoveIconUp = useCallback(() => {
    if (primaryIdx <= 0) return
    const newIcons = [...icons]
    swapIcons(newIcons, primaryIdx, primaryIdx - 1)
    updateIcons(maybeApplyTemplate(newIcons))
    setSelectedIndices([primaryIdx - 1])
  }, [icons, primaryIdx, updateIcons, maybeApplyTemplate, swapIcons])

  const handleMoveIconDown = useCallback(() => {
    if (primaryIdx < 0 || primaryIdx >= icons.length - 1) return
    const newIcons = [...icons]
    swapIcons(newIcons, primaryIdx, primaryIdx + 1)
    updateIcons(maybeApplyTemplate(newIcons))
    setSelectedIndices([primaryIdx + 1])
  }, [icons, primaryIdx, updateIcons, maybeApplyTemplate])

  const handleApplyTemplate = useCallback(() => {
    if (!layout?.template) return
    updateIcons(applyCssTemplate(icons, layout.template))
  }, [icons, layout?.template, updateIcons])

  const handleApplyGrid = useCallback((cols) => {
    if (!layout) return
    const count = icons.length
    if (count === 0 || cols <= 0) return
    const rows = Math.ceil(count / cols)

    // Vanilla 9x3 grid boundaries (game units)
    const vanillaW = 63.45  // 9 * 7.05
    const vanillaH = 21.6   // 3 * 7.2
    const centerX = 0.05
    const centerY = 9.5
    const baseW = 7.05
    const baseH = 7.2

    // Scale each axis independently to fill the vanilla bounding box exactly
    const sx = vanillaW / (cols * baseW)
    const sy = vanillaH / (rows * baseH)

    const newTemplate = {
      ...layout.template,
      iconsPerRow: cols,
      scaleX: sx,
      scaleY: sy,
      iconWidth: baseW,
      iconHeight: baseH,
      centerX,
      centerY
    }
    updateTemplate(newTemplate)
    updateIcons(applyCssTemplate(icons, newTemplate))
  }, [layout, icons, updateIcons, updateTemplate])

  const handleResetVanilla = useCallback(() => {
    fetchLayout()
  }, [])

  if (loading) return <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>Loading CSS layout...</div>
  if (error) return <div style={{ textAlign: 'center', padding: '2rem' }}><p style={{ color: 'var(--color-danger)' }}>{error}</p><button className="mode-btn" onClick={fetchLayout}>Retry</button></div>
  if (!layout) return null

  const selectedIcons = selectedIndices.map(i => icons[i]).filter(Boolean)

  return (
    <div className="sss-layout-editor">
      {/* Top bar */}
      <div className="sss-top-bar">
        <div className="sss-page-tabs">
          <span style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)', fontWeight: 600, padding: '0.35rem 0.5rem', fontSize: '0.85rem' }}>
            Character Select Screen
          </span>
        </div>
        <div className="sss-top-actions">
          <button className="sss-tab-btn" onClick={fetchLayout} onMouseEnter={playHoverSound} title="Reload">&#8635;</button>
          <button
            className={`mode-btn ${dirty ? 'active' : ''}`}
            onClick={handleSave}
            disabled={saving || !dirty}
            onMouseEnter={playHoverSound}
            style={{ marginLeft: '0.5rem' }}
          >
            {saving ? 'Saving...' : dirty ? 'Save *' : 'Saved'}
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="sss-main-content">
        <SssCanvas
          icons={icons}
          selectedIndices={selectedIndices}
          onSelectionChange={handleSelectionChange}
          onMoveIcon={handleMoveIcon}
          onMoveIcons={handleMoveIcons}
          onSwapIcons={handleSwapIcons}
          onContextMenu={(x, y) => setPropsPopup({ x, y })}
          zoom={zoom}
          offset={offset}
          onZoomChange={setZoom}
          onOffsetChange={setOffset}
          showCollision={showCollision}
          showOverscan={showOverscan}
          swapMode={useTemplate}
          API_URL={API_URL}
          iconBaseWidth={CSS_BASE_WIDTH}
          iconBaseHeight={CSS_BASE_HEIGHT}
          templateWidth={CSS_TEMPLATE_WIDTH}
          templateHeight={CSS_TEMPLATE_HEIGHT}
          templateSrc="/css_template.png"
          getCollisionRect={getCssCollisionRect}
          iconEndpoint="/menus/css/fighter-icon"
        />

        <div className="sss-right-panel">
          <div className="sss-icon-actions">
            <button className="sss-action-btn add" onClick={handleAddIcon} onMouseEnter={playHoverSound}>
              + Add Icon
            </button>
            <button className="sss-action-btn remove" onClick={handleRemoveIcon} onMouseEnter={playHoverSound}
              disabled={selectedIndices.length === 0}>
              - Remove{selectedIndices.length > 1 ? ` (${selectedIndices.length})` : ''}
            </button>
          </div>

          <div className="sss-icon-list-header">
            <span>Icons ({icons.length})</span>
            <div className="sss-reorder-btns">
              <button onClick={handleMoveIconUp} title="Move up" disabled={primaryIdx <= 0}>&#9650;</button>
              <button onClick={handleMoveIconDown} title="Move down"
                disabled={primaryIdx < 0 || primaryIdx >= icons.length - 1}>&#9660;</button>
            </div>
          </div>
          <div className="sss-icon-list">
            {icons.map((icon, idx) => (
              <div
                key={idx}
                className={`sss-icon-item ${selectedIndices.includes(idx) ? 'selected' : ''}`}
                onClick={(e) => {
                  playSound('boop')
                  if (e.shiftKey) {
                    const s = new Set(selectedIndices)
                    if (s.has(idx)) s.delete(idx); else s.add(idx)
                    setSelectedIndices([...s])
                  } else {
                    setSelectedIndices([idx])
                  }
                }}
                onContextMenu={(e) => {
                  e.preventDefault()
                  if (!selectedIndices.includes(idx)) setSelectedIndices([idx])
                  setPropsPopup({ x: e.clientX, y: e.clientY })
                }}
              >
                <span className="sss-icon-idx">{idx}</span>
                <span className="sss-icon-name">{icon.fighterName || `Fighter ${icon.fighter}`}</span>
              </div>
            ))}
          </div>
        </div>

        {propsPopup && selectedIcons.length > 0 && (
          <div className="sss-props-popup-overlay" onClick={() => setPropsPopup(null)}>
            <div
              className="sss-props-popup"
              style={{ left: propsPopup.x, top: propsPopup.y }}
              onClick={(e) => e.stopPropagation()}
            >
              <CssIconProperties
                icons={selectedIcons}
                indices={selectedIndices}
                fighters={layout.fighters || []}
                onUpdate={handleUpdateIcon}
              />
            </div>
          </div>
        )}
      </div>

      {/* Bottom toolbar */}
      <div className="sss-bottom-bar">
        <div className="sss-bottom-group">
          <label>Zoom: {zoom}x</label>
          <input type="range" min={4} max={20} value={zoom}
            onChange={(e) => setZoom(parseInt(e.target.value))} style={{ width: '80px' }} />
        </div>
        <label className="sss-checkbox">
          <input type="checkbox" checked={showCollision} onChange={(e) => setShowCollision(e.target.checked)} />
          Collisions
        </label>
        <label className="sss-checkbox">
          <input type="checkbox" checked={showOverscan} onChange={(e) => setShowOverscan(e.target.checked)} />
          Overscan
        </label>
        <label className="sss-checkbox">
          <input type="checkbox" checked={useTemplate} onChange={(e) => handleToggleTemplate(e.target.checked)} />
          Swap Mode
        </label>
        <div className="sss-grid-controls">
          <label>Cols:</label>
          <input type="number" min={1} max={20}
            value={layout?.template?.iconsPerRow ?? 9}
            onChange={(e) => handleApplyGrid(Math.max(1, parseInt(e.target.value) || 1))}
            style={{ width: '42px' }} />
          <span className="sss-grid-dim">
            ({Math.ceil(icons.length / (layout?.template?.iconsPerRow ?? 9))} rows)
          </span>
          <button className="sss-tab-btn" onClick={handleResetVanilla}>Reset</button>
        </div>
      </div>
    </div>
  )
}
