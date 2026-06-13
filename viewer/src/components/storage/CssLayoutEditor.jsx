import { useState, useEffect, useCallback, useRef } from 'react'
import SssCanvas from './SssCanvas'
import CssIconProperties from './CssIconProperties'
import IconReorderList from './IconReorderList'
import PropsPopup from './PropsPopup'
import { playSound, playHoverSound } from '../../utils/sounds'
import { API_URL } from '../../config'
import { applyCssTemplate, buildCssGridTemplate, pickAutoColumns } from '../../utils/cssGridLayout'

// Per-slot layout fields: these stay with the slot position when icon
// identities are reordered/swapped within the list
const CSS_SLOT_FIELDS = ['x', 'y', 'z', 'scaleX', 'scaleY',
  'collisionSizeX', 'collisionSizeY', 'collisionOffsetX', 'collisionOffsetY']

const CSS_BASE_WIDTH = 3.5
const CSS_BASE_HEIGHT = 3.4
const CSS_TEMPLATE_WIDTH = 35.05
const CSS_TEMPLATE_HEIGHT = 28.8

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

  // Drag-and-drop reorder: move the icon identity from one slot to another;
  // the slot layout fields stay with their positions
  const handleReorderIcon = useCallback((from, to) => {
    if (from === to) return
    const slots = icons.map(ic =>
      Object.fromEntries(CSS_SLOT_FIELDS.map(f => [f, ic[f]]))
    )
    const arr = [...icons]
    const [moved] = arr.splice(from, 1)
    arr.splice(to, 0, moved)
    const rezipped = arr.map((ic, i) => ({ ...ic, ...slots[i] }))
    updateIcons(maybeApplyTemplate(rezipped))
    setSelectedIndices([to])
  }, [icons, updateIcons, maybeApplyTemplate])

  const handleApplyTemplate = useCallback(() => {
    if (!layout?.template) return
    updateIcons(applyCssTemplate(icons, layout.template))
  }, [icons, layout?.template, updateIcons])

  const handleApplyGrid = useCallback((cols) => {
    if (!layout) return
    const count = icons.length
    if (count === 0 || cols <= 0) return

    // Scale each axis independently to fill the vanilla bounding box exactly
    const newTemplate = buildCssGridTemplate(layout.template, count, cols)
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
          <IconReorderList
            icons={icons}
            selectedIndices={selectedIndices}
            onSelect={setSelectedIndices}
            onContextMenu={(x, y) => setPropsPopup({ x, y })}
            onReorder={handleReorderIcon}
            getLabel={(icon) => icon.fighterName || `Fighter ${icon.fighter}`}
            getIconUrl={(icon) => icon.iconPath
              ? `${API_URL}/menus/css/fighter-icon?path=${encodeURIComponent(icon.iconPath)}`
              : null}
          />
        </div>

        {propsPopup && selectedIcons.length > 0 && (
          <PropsPopup x={propsPopup.x} y={propsPopup.y} onClose={() => setPropsPopup(null)}>
            <CssIconProperties
              icons={selectedIcons}
              indices={selectedIndices}
              fighters={layout.fighters || []}
              onUpdate={handleUpdateIcon}
            />
          </PropsPopup>
        )}
      </div>

      {/* Bottom toolbar */}
      <div className="sss-bottom-bar">
        {/* Columns is the primary control - big stepper, first in the bar */}
        <div className="sss-grid-controls sss-grid-controls--primary">
          <label>Columns</label>
          <div className="sss-cols-stepper">
            <button
              onClick={() => { playSound('tick'); handleApplyGrid(Math.max(1, (layout?.template?.iconsPerRow ?? 9) - 1)) }}
              disabled={(layout?.template?.iconsPerRow ?? 9) <= 1}
              title="Fewer columns"
            >−</button>
            <input type="number" min={1} max={20}
              value={layout?.template?.iconsPerRow ?? 9}
              onChange={(e) => handleApplyGrid(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))} />
            <button
              onClick={() => { playSound('tick'); handleApplyGrid(Math.min(20, (layout?.template?.iconsPerRow ?? 9) + 1)) }}
              disabled={(layout?.template?.iconsPerRow ?? 9) >= 20}
              title="More columns"
            >+</button>
          </div>
          <span className="sss-grid-dim">
            ({Math.ceil(icons.length / (layout?.template?.iconsPerRow ?? 9))} rows)
          </span>
          <button
            className="sss-tab-btn"
            onClick={() => { playSound('boop'); handleApplyGrid(pickAutoColumns(icons.length)) }}
            title="Auto-fit columns and rows to the icon count"
          >Auto</button>
          <button className="sss-tab-btn" onClick={handleResetVanilla}>Reset</button>
        </div>
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
      </div>
    </div>
  )
}
