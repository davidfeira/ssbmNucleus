/**
 * CharacterMode - MEX character costume management
 *
 * Features:
 * - Fighter list with costume counts
 * - MEX costumes panel with drag-drop reordering
 * - Available costumes panel with batch selection/import
 * - Ice Climbers special handling (auto-pair Popo/Nana)
 * - Single and batch costume import/removal
 * - Extras mode for managing character extras (laser colors, etc.)
 */
import { useState, useEffect } from 'react'
import { getExtraTypes } from '../../config/extraTypes'
import { rgbyToHex } from '../../utils/rgbyColor'

const BACKEND_URL = 'http://127.0.0.1:5000'

export default function CharacterMode({
  fighters,
  selectedFighter,
  onSelectFighter,
  storageCostumes,
  onRefresh,
  refreshing,
  API_URL
}) {
  const [mexCostumes, setMexCostumes] = useState([])
  const [loadingFighter, setLoadingFighter] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importingCostume, setImportingCostume] = useState(null)
  const [removing, setRemoving] = useState(false)
  const [removingCostume, setRemovingCostume] = useState(null)
  const [selectedCostumes, setSelectedCostumes] = useState(new Set())
  const [batchImporting, setBatchImporting] = useState(false)
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 })
  const [draggedIndex, setDraggedIndex] = useState(null)
  const [dragOverIndex, setDragOverIndex] = useState(null)
  const [reordering, setReordering] = useState(false)

  // Extras mode state
  const [extrasMode, setExtrasMode] = useState(false)
  const [selectedExtraType, setSelectedExtraType] = useState(null)
  const [extraMods, setExtraMods] = useState({})
  const [selectedExtraMod, setSelectedExtraMod] = useState(null)
  const [importingExtra, setImportingExtra] = useState(false)

  useEffect(() => {
    if (selectedFighter) {
      fetchMexCostumes(selectedFighter.name, true)
    }
  }, [selectedFighter])

  // Fetch extras when entering extras mode or selecting a type
  useEffect(() => {
    if (extrasMode) {
      fetchExtrasMods()
    }
  }, [extrasMode])

  useEffect(() => {
    if (extrasMode && selectedExtraType) {
      fetchCurrentColors()
    }
  }, [extrasMode, selectedExtraType])

  const [currentColors, setCurrentColors] = useState(null)
  const [isVanilla, setIsVanilla] = useState(true)

  const fetchExtrasMods = async () => {
    // Fetch all mods from vault
    try {
      const response = await fetch(`${API_URL}/storage/extras/list/Falco`)
      const data = await response.json()
      if (data.success) {
        setExtraMods(data.extras || {})
      }
    } catch (err) {
      console.error('Failed to fetch extras:', err)
      setExtraMods({})
    }
  }

  const fetchCurrentColors = async () => {
    // Read actual colors from .dat file
    if (!selectedExtraType) return
    try {
      const response = await fetch(`${API_URL}/storage/extras/current/Falco/${selectedExtraType.id}`)
      const data = await response.json()
      if (data.success) {
        setCurrentColors(data.colors)
        setIsVanilla(data.isVanilla)
      }
    } catch (err) {
      console.error('Failed to fetch current colors:', err)
      setCurrentColors(null)
      setIsVanilla(true)
    }
  }

  const getAllMods = (typeId) => {
    return extraMods[typeId] || []
  }

  const handleImportExtra = async () => {
    if (!selectedExtraMod || !selectedExtraType || importingExtra) return

    setImportingExtra(true)
    try {
      const response = await fetch(`${API_URL}/storage/extras/install`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: 'Falco',
          extraType: selectedExtraType.id,
          modId: selectedExtraMod.id
        })
      })

      const data = await response.json()
      if (data.success) {
        await fetchCurrentColors()
        setSelectedExtraMod(null)
      }
    } catch (err) {
      console.error('Failed to import extra:', err)
    } finally {
      setImportingExtra(false)
    }
  }

  const handleRestoreVanilla = async () => {
    if (!selectedExtraType || importingExtra) return

    setImportingExtra(true)
    try {
      await fetch(`${API_URL}/storage/extras/restore-vanilla`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: 'Falco',
          extraType: selectedExtraType.id
        })
      })
      await fetchCurrentColors()
    } catch (err) {
      console.error('Failed to restore vanilla:', err)
    } finally {
      setImportingExtra(false)
    }
  }

  const fetchMexCostumes = async (fighterName, showLoading = false) => {
    if (showLoading) {
      setLoadingFighter(true)
    }
    try {
      const response = await fetch(`${API_URL}/fighters/${encodeURIComponent(fighterName)}/costumes`)
      const data = await response.json()
      if (data.success) {
        setMexCostumes(data.costumes || [])
      }
    } catch (err) {
      console.error('Failed to fetch MEX costumes:', err)
      setMexCostumes([])
    } finally {
      if (showLoading) {
        setLoadingFighter(false)
      }
    }
  }

  const handleImportCostume = async (costume) => {
    if (importing || importingCostume) {
      console.log('Import already in progress, ignoring click')
      return
    }

    console.log(`=== IMPORT REQUEST ===`)
    console.log(`Costume:`, costume)
    console.log(`Fighter: ${costume.character}`)
    console.log(`Zip Path: ${costume.zipPath}`)

    setImporting(true)
    setImportingCostume(costume.zipPath)

    try {
      // Ice Climbers: Auto-import paired Nana when Popo is selected
      if (costume.isPopo && costume.pairedNanaId) {
        console.log('Ice Climbers Popo detected - will auto-import paired Nana')

        // Find paired Nana costume in storage
        const nanaCostume = storageCostumes.find(c => c.folder === costume.pairedNanaId)

        if (!nanaCostume) {
          console.error('Paired Nana costume not found:', costume.pairedNanaId)
          alert('Paired Nana costume not found in storage')
          return
        }

        // Import Popo first (MEX calls it "Ice Climbers")
        const popoResponse = await fetch(`${API_URL}/import`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            fighter: 'Ice Climbers',
            costumePath: costume.zipPath
          })
        })

        const popoData = await popoResponse.json()
        console.log('Popo import response:', popoData)

        if (!popoData.success) {
          alert(`Popo import failed: ${popoData.error}`)
          return
        }

        // Import Nana second - find Nana fighter (ID 11, could be named "Nana" or "Popo")
        const nanaFighter = fighters.find(f => f.internalId === 11)

        if (!nanaFighter) {
          alert(`Popo imported but could not find Nana fighter (ID 11) in project`)
          return
        }

        console.log(`Importing Nana to fighter: ${nanaFighter.name}`)

        const nanaResponse = await fetch(`${API_URL}/import`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            fighter: nanaFighter.name,
            costumePath: nanaCostume.zipPath
          })
        })

        const nanaData = await nanaResponse.json()
        console.log('Nana import response:', nanaData)

        if (!nanaData.success) {
          alert(`Nana import failed: ${nanaData.error}`)
          return
        }

        console.log(`✓ Successfully imported Ice Climbers pair (Popo + Nana)`)

        // Refresh
        await onRefresh()
        await fetchMexCostumes('Ice Climbers')

      } else {
        // Normal single costume import
        const requestBody = {
          fighter: costume.character,
          costumePath: costume.zipPath
        }

        console.log('Sending import request:', requestBody)

        const response = await fetch(`${API_URL}/import`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody)
        })

        const data = await response.json()
        console.log('Import response:', data)

        if (data.success) {
          console.log(`✓ Successfully imported ${data.result.costumesImported} costume(s) to ${costume.character}`)

          // Refresh
          await onRefresh()
          await fetchMexCostumes(costume.character)
        } else {
          alert(`Import failed: ${data.error}`)
        }
      }
    } catch (err) {
      console.error('Import error:', err)
      alert(`Import error: ${err.message}`)
    } finally {
      setImporting(false)
      setImportingCostume(null)
    }
  }

  const handleRemoveCostume = async (fighterName, costumeIndex, costumeName) => {
    if (removing || removingCostume !== null) {
      console.log('Remove already in progress, ignoring click')
      return
    }

    const isIceClimbers = fighterName === 'Ice Climbers'
    const confirmMessage = isIceClimbers
      ? `Are you sure you want to remove "${costumeName}" (and paired Nana) from Ice Climbers?`
      : `Are you sure you want to remove "${costumeName}" from ${fighterName}?`

    if (!confirm(confirmMessage)) {
      return
    }

    console.log(`=== REMOVE REQUEST ===`)
    console.log(`Fighter: ${fighterName}`)
    console.log(`Costume Index: ${costumeIndex}`)
    console.log(`Costume Name: ${costumeName}`)
    if (isIceClimbers) {
      console.log(`Will also remove paired Nana at index ${costumeIndex}`)
    }

    setRemoving(true)
    setRemovingCostume(costumeIndex)

    try {
      const requestBody = {
        fighter: fighterName,
        costumeIndex: costumeIndex
      }

      console.log('Sending remove request:', requestBody)

      const response = await fetch(`${API_URL}/remove`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      const data = await response.json()
      console.log('Remove response:', data)

      if (!data.success) {
        alert(`Remove failed: ${data.error}`)
        return
      }

      console.log(`✓ Successfully removed "${costumeName}" from ${fighterName}`)

      // Ice Climbers: Also remove paired Nana at same index
      if (isIceClimbers) {
        console.log(`Removing paired Nana at index ${costumeIndex}...`)

        const nanaFighter = fighters.find(f => f.internalId === 11)

        if (!nanaFighter) {
          console.warn('Nana fighter (ID 11) not found in project')
          alert(`Popo removed but could not find Nana fighter in project`)
        } else {
          console.log(`Found Nana fighter named: ${nanaFighter.name}`)

          const nanaRequestBody = {
            fighter: nanaFighter.name,
            costumeIndex: costumeIndex
          }

          const nanaResponse = await fetch(`${API_URL}/remove`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(nanaRequestBody)
          })

          const nanaData = await nanaResponse.json()
          console.log('Nana remove response:', nanaData)

          if (!nanaData.success) {
            alert(`Popo removed but Nana removal failed: ${nanaData.error}`)
          } else {
            console.log(`✓ Successfully removed paired Nana from ${nanaFighter.name}`)
          }
        }
      }

      // Refresh
      await onRefresh()
      await fetchMexCostumes(fighterName)

    } catch (err) {
      console.error('Remove error:', err)
      alert(`Remove error: ${err.message}`)
    } finally {
      setRemoving(false)
      setRemovingCostume(null)
    }
  }

  const handleBatchImport = async () => {
    if (selectedCostumes.size === 0 || batchImporting) return

    setBatchImporting(true)
    const costumesToImport = Array.from(selectedCostumes)
    const total = costumesToImport.length
    setBatchProgress({ current: 0, total })

    let successCount = 0
    let failCount = 0
    const importedNanas = new Set()

    for (let i = 0; i < costumesToImport.length; i++) {
      const zipPath = costumesToImport[i]
      const costume = storageCostumes.find(c => c.zipPath === zipPath)

      if (!costume) {
        failCount++
        continue
      }

      // Skip if this is a Nana that was already imported as part of a Popo pair
      if (importedNanas.has(zipPath)) {
        continue
      }

      setBatchProgress({ current: i + 1, total })

      try {
        // Ice Climbers: Auto-import paired Nana when Popo is selected
        if (costume.isPopo && costume.pairedNanaId) {
          console.log('Ice Climbers Popo detected in batch - will auto-import paired Nana')

          const nanaCostume = storageCostumes.find(c => c.folder === costume.pairedNanaId)

          if (!nanaCostume) {
            console.error('Paired Nana costume not found:', costume.pairedNanaId)
            failCount++
            continue
          }

          // Import Popo first
          const popoResponse = await fetch(`${API_URL}/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              fighter: 'Ice Climbers',
              costumePath: costume.zipPath
            })
          })

          const popoData = await popoResponse.json()

          if (!popoData.success) {
            console.error(`Popo import failed: ${popoData.error}`)
            failCount++
            continue
          }

          // Import Nana second
          const nanaFighter = fighters.find(f => f.internalId === 11)

          if (!nanaFighter) {
            console.error('Nana fighter (ID 11) not found in project')
            failCount++
            continue
          }

          const nanaResponse = await fetch(`${API_URL}/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              fighter: nanaFighter.name,
              costumePath: nanaCostume.zipPath
            })
          })

          const nanaData = await nanaResponse.json()

          if (!nanaData.success) {
            console.error(`Nana import failed: ${nanaData.error}`)
            failCount++
            continue
          }

          console.log(`✓ Successfully imported Ice Climbers pair (Popo + Nana)`)
          successCount++

          // Mark this Nana as imported
          importedNanas.add(nanaCostume.zipPath)

        } else {
          // Normal single costume import
          const requestBody = {
            fighter: costume.character,
            costumePath: costume.zipPath
          }

          const response = await fetch(`${API_URL}/import`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
          })

          const data = await response.json()

          if (data.success) {
            successCount++
          } else {
            console.error(`Import failed for ${costume.name}:`, data.error)
            failCount++
          }
        }
      } catch (err) {
        console.error(`Import error for ${costume.name}:`, err)
        failCount++
      }
    }

    // Refresh once at the end
    await onRefresh()
    if (selectedFighter) {
      await fetchMexCostumes(selectedFighter.name)
    }

    // Clear selections
    setSelectedCostumes(new Set())
    setBatchImporting(false)
    setBatchProgress({ current: 0, total: 0 })

    // Show summary
    if (failCount > 0) {
      alert(`Batch import completed:\n${successCount} succeeded, ${failCount} failed`)
    } else {
      console.log(`✓ Successfully imported ${successCount} costume(s)`)
    }
  }

  // Drag and Drop Handlers
  const handleDragStart = (e, index) => {
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDragEnter = (e, index) => {
    e.preventDefault()
    setDragOverIndex(index)
  }

  const handleDragLeave = (e) => {
    if (e.currentTarget === e.target) {
      setDragOverIndex(null)
    }
  }

  const handleDrop = async (e, toIndex) => {
    e.preventDefault()

    if (draggedIndex === null || draggedIndex === toIndex || reordering) {
      return
    }

    const fromIndex = draggedIndex

    // Optimistically update UI
    const newCostumes = [...mexCostumes]
    const [movedItem] = newCostumes.splice(fromIndex, 1)
    newCostumes.splice(toIndex, 0, movedItem)
    setMexCostumes(newCostumes)

    // Clear drag state
    setDraggedIndex(null)
    setDragOverIndex(null)

    setReordering(true)

    try {
      const response = await fetch(`${API_URL}/reorder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fighter: selectedFighter.name,
          fromIndex: fromIndex,
          toIndex: toIndex
        })
      })

      const data = await response.json()

      if (data.success) {
        console.log(`✓ Successfully reordered costume from ${fromIndex} to ${toIndex}`)
        await fetchMexCostumes(selectedFighter.name)
      } else {
        alert(`Reorder failed: ${data.error}`)
        await fetchMexCostumes(selectedFighter.name)
      }
    } catch (err) {
      console.error('Reorder error:', err)
      alert(`Reorder error: ${err.message}`)
      await fetchMexCostumes(selectedFighter.name)
    } finally {
      setReordering(false)
    }
  }

  const handleDragEnd = () => {
    setDraggedIndex(null)
    setDragOverIndex(null)
  }

  const getCostumesForFighter = (fighterName) => {
    return storageCostumes.filter(c => c.character === fighterName && !c.isNana)
  }

  const toggleCostumeSelection = (zipPath) => {
    setSelectedCostumes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(zipPath)) {
        newSet.delete(zipPath)
      } else {
        newSet.add(zipPath)
      }
      return newSet
    })
  }

  const selectAllCostumes = () => {
    if (!selectedFighter) return
    const allCostumes = getCostumesForFighter(selectedFighter.name)
    setSelectedCostumes(prev => {
      const newSet = new Set(prev)
      allCostumes.forEach(c => newSet.add(c.zipPath))
      return newSet
    })
  }

  const clearSelection = () => {
    setSelectedCostumes(new Set())
  }

  // Laser beam preview component for extras
  const LaserBeamPreview = ({ modifications, compact = false }) => {
    const getColor = (layerId) => {
      const mod = modifications?.[layerId]
      if (!mod?.color) return null
      // Center layer is RGB format, others are RGBY
      if (layerId === 'center') {
        return `#${mod.color}`
      }
      return rgbyToHex(mod.color)
    }

    const wide = getColor('wide') || '#ff0000'
    const thin = getColor('thin') || '#ff0000'
    const outline = getColor('outline') || '#ff0000'
    const center = getColor('center') || '#ffffff'
    const height = compact ? 40 : 50

    return (
      <div style={{
        position: 'relative',
        height: `${height}px`,
        width: '100%',
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute', left: '8%', right: '8%',
          height: compact ? '24px' : '30px', borderRadius: '100px',
          background: `linear-gradient(90deg, transparent 0%, ${wide} 5%, ${wide} 95%, transparent 100%)`,
          boxShadow: `0 0 15px ${wide}50, 0 0 30px ${wide}30`, opacity: 0.5
        }} />
        <div style={{
          position: 'absolute', left: '8%', right: '8%',
          height: compact ? '14px' : '18px', borderRadius: '100px',
          background: `linear-gradient(90deg, transparent 0%, ${thin} 3%, ${thin} 97%, transparent 100%)`,
          boxShadow: `0 0 8px ${thin}70`, opacity: 0.7
        }} />
        <div style={{
          position: 'absolute', left: '8%', right: '8%',
          height: compact ? '8px' : '10px', borderRadius: '100px',
          background: `linear-gradient(90deg, transparent 0%, ${outline} 2%, ${outline} 98%, transparent 100%)`,
          boxShadow: `0 0 5px ${outline}90`, opacity: 0.9
        }} />
        <div style={{
          position: 'absolute', left: '8%', right: '8%',
          height: '3px', borderRadius: '100px',
          background: `linear-gradient(90deg, transparent 0%, ${center} 2%, ${center} 98%, transparent 100%)`,
          boxShadow: `0 0 3px ${center}`
        }} />
      </div>
    )
  }

  // Convert currentColors (object from API) to modifications format for LaserBeamPreview
  const currentColorsToMods = (colors) => {
    if (!colors) return null
    const mods = {}
    for (const [key, value] of Object.entries(colors)) {
      mods[key] = { color: value }
    }
    return mods
  }

  // Extras mode UI
  if (extrasMode) {
    const extraTypes = getExtraTypes('Falco')

    return (
      <div className="mex-content">
        <div className="fighters-list">
          <h3>Extras</h3>
          <div className="fighter-items">
            {extraTypes.map(extraType => (
              <div
                key={extraType.id}
                className={`fighter-item ${selectedExtraType?.id === extraType.id ? 'selected' : ''}`}
                onClick={() => setSelectedExtraType(extraType)}
              >
                <div className="fighter-content">
                  <div className="fighter-name">{extraType.name}</div>
                  <div className="fighter-info">
                    <span className="costume-count">
                      {(extraMods[extraType.id] || []).length} in vault
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="costumes-panel">
          {selectedExtraType ? (
            <>
              {/* Currently in MEX section - shows actual colors from .dat */}
              <div className="costumes-section">
                <h3>Currently in MEX</h3>
                <div className="costume-list existing">
                  <div className={`costume-card existing-costume ${isVanilla ? 'vanilla-extra' : ''}`}>
                    <div className="costume-preview" style={{ padding: '8px' }}>
                      {currentColors ? (
                        <LaserBeamPreview modifications={currentColorsToMods(currentColors)} compact />
                      ) : (
                        <div className="vanilla-preview"><span>Loading...</span></div>
                      )}
                      {!isVanilla && (
                        <button
                          className="btn-remove"
                          onClick={handleRestoreVanilla}
                          disabled={importingExtra}
                          title="Restore vanilla"
                        >
                          ×
                        </button>
                      )}
                    </div>
                    <div className="costume-info">
                      <h4>{isVanilla ? 'Vanilla' : 'Custom'}</h4>
                    </div>
                  </div>
                </div>
              </div>

              {/* Available to Import section - shows ALL mods */}
              <div className="costumes-section">
                <div className="costumes-section-header">
                  <h3>Available to Import</h3>
                  <div className="batch-controls">
                    {selectedExtraMod && (
                      <button
                        className="btn-batch-import"
                        onClick={handleImportExtra}
                        disabled={importingExtra}
                      >
                        {importingExtra ? 'Importing...' : 'Import Selected'}
                      </button>
                    )}
                    <button
                      className="btn-back"
                      onClick={() => { setExtrasMode(false); setSelectedExtraType(null); setSelectedExtraMod(null); setCurrentColors(null) }}
                    >
                      ← Back
                    </button>
                  </div>
                </div>
                <div className="costume-list">
                  {getAllMods(selectedExtraType.id).map(mod => (
                    <div
                      key={mod.id}
                      className={`costume-card ${selectedExtraMod?.id === mod.id ? 'selected' : ''}`}
                      onClick={() => setSelectedExtraMod(mod)}
                    >
                      <div className="costume-preview" style={{ padding: '8px' }}>
                        <LaserBeamPreview modifications={mod.modifications} compact />
                        <input
                          type="checkbox"
                          className="costume-checkbox"
                          checked={selectedExtraMod?.id === mod.id}
                          readOnly
                        />
                      </div>
                      <div className="costume-info">
                        <h4>{mod.name}</h4>
                      </div>
                    </div>
                  ))}
                  {getAllMods(selectedExtraType.id).length === 0 && (
                    <div className="no-costumes">
                      <p>No extras in vault. Create some in Storage → Falco → Extras.</p>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="no-selection">
              <p>Select an extra type</p>
            </div>
          )}
        </div>

        {/* Import Loading Overlay */}
        {importingExtra && (
          <div className="import-overlay">
            <div className="import-modal">
              <div className="import-spinner"></div>
              <h3>Importing...</h3>
              <p>Please wait...</p>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Character mode UI (default)
  return (
    <div className="mex-content">
      <div className="fighters-list">
        <h3>Fighters ({fighters.length})</h3>
        <div className="fighter-items">
          {fighters.map(fighter => {
            const availableCostumes = getCostumesForFighter(fighter.name)
            return (
              <div
                key={fighter.internalId}
                className={`fighter-item ${selectedFighter?.internalId === fighter.internalId ? 'selected' : ''}`}
                onClick={() => onSelectFighter(fighter)}
              >
                {fighter.defaultStockUrl && (
                  <img
                    src={`${BACKEND_URL}${fighter.defaultStockUrl}`}
                    alt=""
                    className="fighter-stock-icon"
                    onError={(e) => e.target.style.display = 'none'}
                  />
                )}
                <div className="fighter-content">
                  <div className="fighter-name">{fighter.name}</div>
                  <div className="fighter-info">
                    <span className="costume-count">{fighter.costumeCount} in MEX</span>
                    {availableCostumes.length > 0 && (
                      <span className="available-count">{availableCostumes.length} available</span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className={`costumes-panel ${refreshing || loadingFighter ? 'refreshing' : ''}`}>
        {selectedFighter ? (
          <>
            <div className="costumes-section">
              <h3>Already in MEX ({mexCostumes.length})</h3>
              <div className={`costume-list existing ${reordering ? 'processing' : ''} ${loadingFighter ? 'processing' : ''}`}>
                {mexCostumes.map((costume, idx) => {
                  const isDragging = draggedIndex === idx
                  const isDragOver = dragOverIndex === idx
                  return (
                    <div
                      key={idx}
                      className={`costume-card existing-costume ${isDragging ? 'dragging' : ''} ${isDragOver ? 'drag-over' : ''}`}
                      draggable={!removing && !reordering}
                      onDragStart={(e) => handleDragStart(e, idx)}
                      onDragOver={handleDragOver}
                      onDragEnter={(e) => handleDragEnter(e, idx)}
                      onDragLeave={handleDragLeave}
                      onDrop={(e) => handleDrop(e, idx)}
                      onDragEnd={handleDragEnd}
                    >
                      {costume.cspUrl && (
                        <div className="costume-preview">
                          <img
                            src={`${API_URL.replace('/api/mex', '')}${costume.cspUrl}`}
                            alt={costume.name}
                            onError={(e) => e.target.style.display = 'none'}
                          />
                          <button
                            className="btn-remove"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleRemoveCostume(selectedFighter.name, idx, costume.name)
                            }}
                            disabled={removing}
                            title="Remove costume"
                          >
                            ×
                          </button>
                        </div>
                      )}
                      <div className="costume-info">
                        <h4>{costume.name}</h4>
                        {costume.iconUrl && (
                          <div className="costume-assets">
                            <div className="stock-icon">
                              <img
                                src={`${API_URL.replace('/api/mex', '')}${costume.iconUrl}`}
                                alt="Stock"
                                onError={(e) => e.target.style.display = 'none'}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
                {mexCostumes.length === 0 && (
                  <div className="no-costumes">
                    <p>No costumes in MEX yet</p>
                  </div>
                )}
              </div>
            </div>

            <div className="costumes-section">
              <div className="costumes-section-header">
                <h3>
                  Available to Import
                  {selectedCostumes.size > 0 && ` (${selectedCostumes.size} total selected)`}
                </h3>
                <div className="batch-controls">
                  {getCostumesForFighter(selectedFighter.name).length > 0 && (
                    <button
                      className="btn-select-all"
                      onClick={selectAllCostumes}
                      disabled={loadingFighter || batchImporting}
                    >
                      Select All
                    </button>
                  )}
                  {selectedCostumes.size > 0 && (
                    <>
                      <button
                        className="btn-batch-import"
                        onClick={handleBatchImport}
                        disabled={batchImporting || loadingFighter}
                      >
                        {batchImporting
                          ? `Importing ${batchProgress.current}/${batchProgress.total}...`
                          : `Import All Selected (${selectedCostumes.size})`}
                      </button>
                      <button
                        className="btn-clear-selection"
                        onClick={clearSelection}
                        disabled={batchImporting || loadingFighter}
                      >
                        Clear
                      </button>
                    </>
                  )}
                  <button
                    className="btn-extras-mode"
                    onClick={() => setExtrasMode(true)}
                  >
                    Extras
                  </button>
                </div>
              </div>
              <div className={`costume-list ${loadingFighter ? 'processing' : ''}`}>
                {getCostumesForFighter(selectedFighter.name).map((costume, idx) => {
                  const isSelected = selectedCostumes.has(costume.zipPath)
                  return (
                    <div
                      key={idx}
                      className={`costume-card ${isSelected ? 'selected' : ''}`}
                      onClick={() => !batchImporting && !loadingFighter && toggleCostumeSelection(costume.zipPath)}
                    >
                      <div className="costume-preview">
                        {costume.cspUrl && (
                          <img
                            src={`${API_URL.replace('/api/mex', '')}${costume.cspUrl}`}
                            alt={costume.name}
                            onError={(e) => e.target.style.display = 'none'}
                          />
                        )}
                        <input
                          type="checkbox"
                          className="costume-checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          disabled={batchImporting || loadingFighter}
                        />
                      </div>
                      <div className="costume-info">
                        <h4>{costume.name?.includes(' - ') ? costume.name.split(' - ').slice(1).join(' - ') : costume.name}</h4>
                        <div className="costume-assets">
                          {costume.stockUrl && (
                            <div className="stock-icon">
                              <img
                                src={`${API_URL.replace('/api/mex', '')}${costume.stockUrl}`}
                                alt="Stock"
                                onError={(e) => e.target.style.display = 'none'}
                              />
                            </div>
                          )}
                          {costume.slippiSafe && (
                            <div className="slippi-badge" title="Slippi Safe">
                              ✓
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
                {getCostumesForFighter(selectedFighter.name).length === 0 && (
                  <div className="no-costumes">
                    <p>No costumes available in storage for {selectedFighter.name}</p>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="no-selection">
            <p>Select a fighter to view costumes</p>
          </div>
        )}
      </div>

      {/* Import Loading Overlay */}
      {(importing || batchImporting) && (
        <div className="import-overlay">
          <div className="import-modal">
            <div className="import-spinner"></div>
            <h3>Importing...</h3>
            {batchImporting && batchProgress.total > 0 && (
              <div className="import-progress">
                <div
                  className="import-progress-bar"
                  style={{ width: `${(batchProgress.current / batchProgress.total) * 100}%` }}
                />
              </div>
            )}
            <p>{batchImporting && batchProgress.total > 0
              ? `${batchProgress.current} of ${batchProgress.total} costumes`
              : 'Please wait...'}</p>
          </div>
        </div>
      )}
    </div>
  )
}
