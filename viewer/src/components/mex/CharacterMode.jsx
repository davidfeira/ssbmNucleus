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
import { useState, useEffect, useRef } from 'react'
import { getExtraTypes, hasExtras } from '../../config/extraTypes'
import { rgbyToHex } from '../../utils/rgbyColor'
import { playSound, playHoverSound } from '../../utils/sounds'
import ConfirmDialog from '../shared/ConfirmDialog'
import { BACKEND_URL } from '../../config'

export default function CharacterMode({
  mode,
  onModeChange,
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
  const [dataReady, setDataReady] = useState(false)
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

  // Confirm dialog state for removing costumes
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [pendingRemoval, setPendingRemoval] = useState(null)

  // Team color state
  const [teamColors, setTeamColors] = useState({ red: null, blue: null, green: null })
  const [selectedTeamColor, setSelectedTeamColor] = useState(null)

  // Ref for scrolling Available to Import list to top on character change
  const availableListRef = useRef(null)

  useEffect(() => {
    if (selectedFighter) {
      // Clear old data immediately for clean transition
      setDataReady(false)
      setMexCostumes([])
      setSelectedTeamColor(null)
      fetchMexCostumes(selectedFighter.name, true)
      fetchTeamColors(selectedFighter.name)
      // Reset scroll position of Available to Import list
      if (availableListRef.current) {
        availableListRef.current.scrollTop = 0
      }
    }
  }, [selectedFighter])

  // Fetch extras when entering extras mode or selecting a type
  useEffect(() => {
    if (extrasMode && selectedFighter) {
      fetchExtrasMods()
    }
  }, [extrasMode, selectedFighter])

  useEffect(() => {
    if (extrasMode && selectedExtraType && selectedFighter) {
      fetchCurrentColors()
    }
  }, [extrasMode, selectedExtraType, selectedFighter])

  const [currentColors, setCurrentColors] = useState(null)
  const [isVanilla, setIsVanilla] = useState(true)

  const fetchExtrasMods = async () => {
    // Fetch all mods from vault
    if (!selectedFighter) return
    try {
      const response = await fetch(`${API_URL}/storage/extras/list/${selectedFighter.name}`)
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
    if (!selectedExtraType || !selectedFighter) return
    try {
      const response = await fetch(`${API_URL}/storage/extras/current/${selectedFighter.name}/${selectedExtraType.id}`)
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
    if (!selectedExtraMod || !selectedExtraType || importingExtra || !selectedFighter) return

    setImportingExtra(true)
    try {
      // Use different endpoint for model types vs hex types
      const isModelType = selectedExtraType.type === 'model'
      const endpoint = isModelType
        ? `${API_URL}/storage/models/install`
        : `${API_URL}/storage/extras/install`

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedFighter.name,
          extraType: selectedExtraType.id,
          modId: selectedExtraMod.id
        })
      })

      const data = await response.json()
      if (data.success) {
        if (!isModelType) {
          await fetchCurrentColors()
        } else {
          // Only show alert for model types since we can't preview them
          alert(`Successfully installed ${selectedExtraMod.name}!`)
        }
        setSelectedExtraMod(null)
      } else {
        alert(`Install failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Failed to import extra:', err)
      alert(`Install error: ${err.message}`)
    } finally {
      setImportingExtra(false)
    }
  }

  const handleRestoreVanilla = async () => {
    if (!selectedExtraType || importingExtra || !selectedFighter) return

    setImportingExtra(true)
    try {
      await fetch(`${API_URL}/storage/extras/restore-vanilla`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character: selectedFighter.name,
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
        // Small delay to let React render, then trigger cascade
        setTimeout(() => setDataReady(true), 50)
      }
    }
  }

  const fetchTeamColors = async (fighterName) => {
    try {
      const response = await fetch(`${API_URL}/fighters/${encodeURIComponent(fighterName)}/team-colors`)
      const data = await response.json()
      if (data.success) {
        setTeamColors({
          red: data.red,
          blue: data.blue,
          green: data.green
        })
      }
    } catch (err) {
      console.error('Failed to fetch team colors:', err)
      setTeamColors({ red: null, blue: null, green: null })
    }
  }

  const handleTeamColorClick = (color) => {
    playSound('boop')
    setSelectedTeamColor(selectedTeamColor === color ? null : color)
  }

  const handleCostumeTeamAssign = async (costumeIndex) => {
    if (!selectedTeamColor || !selectedFighter) return

    try {
      const response = await fetch(`${API_URL}/fighters/${encodeURIComponent(selectedFighter.name)}/team-colors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          color: selectedTeamColor,
          costumeIndex: costumeIndex
        })
      })

      const data = await response.json()
      if (data.success) {
        playSound('newSkin')
        await fetchTeamColors(selectedFighter.name)
        setSelectedTeamColor(null)
      } else {
        console.error('Failed to set team color:', data.error)
      }
    } catch (err) {
      console.error('Failed to set team color:', err)
    }
  }

  // Get the team color assigned to a costume index
  const getCostumeTeamColor = (costumeIndex) => {
    const colors = []
    if (teamColors.red === costumeIndex) colors.push('red')
    if (teamColors.blue === costumeIndex) colors.push('blue')
    if (teamColors.green === costumeIndex) colors.push('green')
    return colors
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

  const handleRemoveCostume = (fighterName, costumeIndex, costumeName) => {
    if (removing || removingCostume !== null) {
      console.log('Remove already in progress, ignoring click')
      return
    }

    const isIceClimbers = fighterName === 'Ice Climbers'
    const confirmMessage = isIceClimbers
      ? `Are you sure you want to remove "${costumeName}" (and paired Nana) from Ice Climbers?`
      : `Are you sure you want to remove "${costumeName}" from ${fighterName}?`

    // Show confirm dialog instead of native confirm()
    setPendingRemoval({ fighterName, costumeIndex, costumeName, isIceClimbers })
    setShowConfirmDialog(true)
  }

  const confirmRemoveCostume = async () => {
    if (!pendingRemoval) return

    const { fighterName, costumeIndex, costumeName, isIceClimbers } = pendingRemoval
    setShowConfirmDialog(false)
    setPendingRemoval(null)

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
      playSound('error')
      alert(`Batch import completed:\n${successCount} succeeded, ${failCount} failed`)
    } else {
      playSound('newSkin')
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
        playSound('boop')
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

  // Side-B preview component for extras
  const SideBPreview = ({ modifications, compact = false }) => {
    const getColor = (layerId) => {
      const mod = modifications?.[layerId]
      if (!mod?.color) return null
      // RGBA format: first 6 chars are RGB
      const hex = mod.color.substring(0, 6)
      return `#${hex}`
    }

    const primary = getColor('primary') || '#0099FF'
    const secondary = getColor('secondary') || '#CCE6FF'
    const tertiary = getColor('tertiary') || '#FFFFFF'
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
        overflow: 'hidden',
        padding: '0 8px'
      }}>
        {[0.15, 0.3, 0.5, 0.7].map((opacity, i) => (
          <div key={i} style={{
            position: 'absolute',
            left: `${10 + i * 18}%`,
            width: compact ? '16px' : '20px',
            height: compact ? '24px' : '30px',
            borderRadius: '4px',
            background: `linear-gradient(135deg, ${primary} 0%, ${secondary} 50%, ${tertiary} 100%)`,
            opacity: opacity,
            boxShadow: `0 0 ${8 + i * 4}px ${primary}40`
          }} />
        ))}
        <div style={{
          position: 'absolute',
          right: '12%',
          width: compact ? '20px' : '24px',
          height: compact ? '28px' : '34px',
          borderRadius: '4px',
          background: `linear-gradient(135deg, ${primary} 0%, ${secondary} 50%, ${tertiary} 100%)`,
          boxShadow: `0 0 12px ${primary}60, 0 0 20px ${secondary}40`
        }} />
      </div>
    )
  }

  // Up-B preview component for Firefox/Firebird flame (all colors)
  const UpBPreview = ({ modifications, compact = false }) => {
    const tipColor = modifications?.tip?.color ? rgbyToHex(modifications.tip.color) : '#FF6600'
    const bodyColor = modifications?.body?.color ? `#${modifications.body.color}` : '#FFFFFF'
    const trailColor = modifications?.trail?.color ? `#${modifications.trail.color}` : '#FFFFFF'
    const ringsColor = modifications?.rings?.color ? `#${modifications.rings.color}` : '#FFFF00'

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
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        {/* Fire ring */}
        <div style={{
          position: 'absolute',
          width: compact ? '50px' : '60px',
          height: compact ? '16px' : '20px',
          bottom: compact ? '8px' : '10px',
          borderRadius: '50%',
          border: `2px solid ${ringsColor}`,
          boxShadow: `0 0 6px ${ringsColor}`,
          opacity: 0.6
        }} />
        {/* Body glow */}
        <div style={{
          position: 'absolute',
          width: compact ? '24px' : '30px',
          height: compact ? '40px' : '50px',
          bottom: compact ? '5px' : '5px',
          background: `radial-gradient(ellipse at center, ${bodyColor}30 0%, transparent 70%)`,
          filter: `drop-shadow(0 0 8px ${bodyColor}40)`
        }} />
        {/* Trail particles */}
        {[0.3, 0.5].map((opacity, i) => (
          <div key={i} style={{
            position: 'absolute',
            width: '6px',
            height: '6px',
            bottom: `${compact ? 20 : 25 + i * 10}px`,
            left: `${45 + (i % 2 ? 5 : -5)}%`,
            borderRadius: '50%',
            background: trailColor,
            opacity: opacity,
            boxShadow: `0 0 3px ${trailColor}`
          }} />
        ))}
        {/* Main flame */}
        <div style={{
          position: 'absolute',
          width: compact ? '18px' : '22px',
          height: compact ? '28px' : '34px',
          bottom: compact ? '2px' : '0',
          borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
          background: `linear-gradient(to top, ${tipColor} 0%, ${tipColor}CC 40%, ${tipColor}66 70%, transparent 100%)`,
          filter: `drop-shadow(0 0 5px ${tipColor})`
        }} />
        {/* Inner core */}
        <div style={{
          position: 'absolute',
          width: compact ? '8px' : '10px',
          height: compact ? '14px' : '18px',
          bottom: compact ? '4px' : '3px',
          borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
          background: `linear-gradient(to top, #FFFFFF 0%, ${tipColor} 60%, transparent 100%)`
        }} />
      </div>
    )
  }

  // Laser Ring preview component for Fox/Falco laser hit ring effect
  const LaserRingPreview = ({ modifications, compact = false }) => {
    const color1 = modifications?.color1?.color ? `#${modifications.color1.color}` : '#FF004C'
    const color2 = modifications?.color2?.color ? `#${modifications.color2.color}` : '#B20000'
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
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        {/* Outer glow - secondary color */}
        <div style={{
          position: 'absolute',
          width: compact ? '50px' : '60px',
          height: compact ? '50px' : '60px',
          borderRadius: '50%',
          background: `radial-gradient(ellipse at center, ${color2}40 0%, transparent 70%)`,
          filter: `drop-shadow(0 0 10px ${color2}50)`
        }} />
        {/* Main ring - primary color */}
        <div style={{
          position: 'absolute',
          width: compact ? '38px' : '46px',
          height: compact ? '38px' : '46px',
          borderRadius: '50%',
          border: `3px solid ${color1}`,
          boxShadow: `0 0 10px ${color1}, inset 0 0 10px ${color1}40`
        }} />
        {/* Inner ring - primary color */}
        <div style={{
          position: 'absolute',
          width: compact ? '20px' : '24px',
          height: compact ? '20px' : '24px',
          borderRadius: '50%',
          border: `2px solid ${color1}`,
          opacity: 0.6
        }} />
        {/* Center dot - primary color */}
        <div style={{
          position: 'absolute',
          width: compact ? '6px' : '8px',
          height: compact ? '6px' : '8px',
          borderRadius: '50%',
          background: color1,
          boxShadow: `0 0 5px ${color1}`
        }} />
      </div>
    )
  }

  // Shine preview component for reflector shield (two-color gradient)
  const ShinePreview = ({ modifications, compact = false }) => {
    // Get colors from modifications (new two-color gradient format)
    const primaryColor = modifications?.primary?.color ? rgbyToHex(modifications.primary.color) : '#0066FF'
    const secondaryColor = modifications?.secondary?.color ? rgbyToHex(modifications.secondary.color) : '#8888AA'

    const size = compact ? 36 : 50

    return (
      <div style={{
        position: 'relative',
        height: `${size}px`,
        width: '100%',
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        {/* Outer glow using primary */}
        <div style={{
          position: 'absolute',
          width: compact ? '45px' : '60px',
          height: compact ? '45px' : '60px',
          background: `radial-gradient(ellipse at center, ${primaryColor}50 0%, transparent 70%)`,
          filter: `drop-shadow(0 0 10px ${primaryColor}60)`
        }} />
        {/* Fill glow using secondary */}
        <div style={{
          position: 'absolute',
          width: compact ? '35px' : '45px',
          height: compact ? '35px' : '45px',
          background: `radial-gradient(ellipse at center, ${secondaryColor}80 0%, ${secondaryColor}40 40%, transparent 70%)`
        }} />
        {/* Hexagon with gradient from secondary (fill) to primary (edge) */}
        <div style={{
          position: 'absolute',
          width: compact ? '26px' : '34px',
          height: compact ? '26px' : '34px',
          background: `radial-gradient(circle at center, ${secondaryColor} 30%, ${primaryColor} 100%)`,
          clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
          opacity: 0.9,
          boxShadow: `0 0 8px ${primaryColor}`
        }} />
        {/* Edge highlight */}
        <div style={{
          position: 'absolute',
          width: compact ? '28px' : '36px',
          height: compact ? '28px' : '36px',
          border: `2px solid ${primaryColor}`,
          clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
          opacity: 0.7
        }} />
      </div>
    )
  }

  // Sword preview component for sword trail
  const SwordPreview = ({ modifications, compact = false }) => {
    const mainColor = modifications?.main?.color ? `#${modifications.main.color}` : '#FF0000'
    const secondaryColor = modifications?.secondary?.color ? `#${modifications.secondary.color}` : '#FFFF00'
    const tertiaryColor = modifications?.tertiary?.color ? `#${modifications.tertiary.color}` : '#FFFFFF'

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
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        <svg width={compact ? 80 : 100} height={compact ? 35 : 45} viewBox="0 0 100 45" style={{ overflow: 'visible' }}>
          {/* Outer edge (tertiary) */}
          <path
            d="M 5 40 Q 50 0 95 40"
            fill="none"
            stroke={tertiaryColor}
            strokeWidth={compact ? 12 : 14}
            strokeLinecap="round"
            opacity="0.5"
          />
          {/* Middle (secondary) */}
          <path
            d="M 5 40 Q 50 0 95 40"
            fill="none"
            stroke={secondaryColor}
            strokeWidth={compact ? 7 : 9}
            strokeLinecap="round"
            opacity="0.7"
          />
          {/* Inner core (main) */}
          <path
            d="M 5 40 Q 50 0 95 40"
            fill="none"
            stroke={mainColor}
            strokeWidth={compact ? 3 : 4}
            strokeLinecap="round"
          />
        </svg>
      </div>
    )
  }

  // Dual color preview for 2-color effects (punch, thunder, fireball, shadow ball)
  const DualColorPreview = ({ extraType, modifications, compact = false }) => {
    // Get colors - handle both color1/color2 and tip_color1/tip_color2 formats
    const color1 = modifications?.color1?.color || modifications?.tip_color1?.color || 'FFFFFF'
    const color2 = modifications?.color2?.color || modifications?.tip_color2?.color || '0000FF'
    const color1Hex = `#${color1}`
    const color2Hex = `#${color2}`

    const height = compact ? 40 : 50

    // Punch effect - explosion/flame burst
    if (extraType?.id === 'falcon_punch' || extraType?.id === 'warlock_punch') {
      return (
        <div style={{
          position: 'relative',
          height: `${height}px`,
          width: '100%',
          background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden'
        }}>
          <svg width={compact ? 80 : 100} height={compact ? 36 : 45} viewBox="0 0 100 45">
            <ellipse cx="50" cy="22" rx="40" ry="18" fill={color2Hex} opacity="0.3" />
            <ellipse cx="50" cy="22" rx="28" ry="12" fill={color1Hex} opacity="0.6" />
            <ellipse cx="50" cy="22" rx="15" ry="6" fill={color1Hex} />
          </svg>
        </div>
      )
    }

    // Thunder effect - lightning bolt
    if (extraType?.id === 'thunder' || extraType?.id === 'pk_thunder') {
      return (
        <div style={{
          position: 'relative',
          height: `${height}px`,
          width: '100%',
          background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden'
        }}>
          <svg width={compact ? 60 : 80} height={compact ? 36 : 45} viewBox="0 0 80 45">
            <path d="M42 3 L28 18 L38 18 L24 42 L56 22 L44 22 L58 3 Z"
              fill={color2Hex} opacity="0.4" transform="scale(1.1) translate(-4, -2)" />
            <path d="M42 3 L28 18 L38 18 L24 42 L56 22 L44 22 L58 3 Z"
              fill={color1Hex} />
          </svg>
        </div>
      )
    }

    // Fireball effect
    if (extraType?.id === 'fireball') {
      return (
        <div style={{
          position: 'relative',
          height: `${height}px`,
          width: '100%',
          background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden'
        }}>
          <svg width={compact ? 60 : 80} height={compact ? 36 : 45} viewBox="0 0 80 45">
            <circle cx="40" cy="22" r="18" fill={color2Hex} opacity="0.4" />
            <circle cx="40" cy="22" r="12" fill={color1Hex} opacity="0.7" />
            <circle cx="40" cy="22" r="6" fill={color1Hex} />
          </svg>
        </div>
      )
    }

    // Shadow Ball effect
    if (extraType?.id === 'shadow_ball') {
      return (
        <div style={{
          position: 'relative',
          height: `${height}px`,
          width: '100%',
          background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden'
        }}>
          <svg width={compact ? 60 : 80} height={compact ? 36 : 45} viewBox="0 0 80 45">
            <circle cx="40" cy="22" r="18" fill={color2Hex} opacity="0.3" />
            <circle cx="40" cy="22" r="13" fill={color1Hex} opacity="0.5" />
            <circle cx="40" cy="22" r="7" fill={color1Hex} />
          </svg>
        </div>
      )
    }

    // Default dual-color
    return (
      <div style={{
        position: 'relative',
        height: `${height}px`,
        width: '100%',
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        <svg width={compact ? 80 : 100} height={compact ? 36 : 45} viewBox="0 0 100 45">
          <circle cx="35" cy="22" r="14" fill={color1Hex} />
          <circle cx="65" cy="22" r="14" fill={color2Hex} />
        </svg>
      </div>
    )
  }

  // Model preview for 3D model extras (gun, etc.)
  const ModelPreview = ({ mod, compact = false }) => {
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
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        {/* 3D cube icon */}
        <svg
          width={compact ? 24 : 32}
          height={compact ? 24 : 32}
          viewBox="0 0 24 24"
          fill="none"
          stroke="#4a9eff"
          strokeWidth="1.5"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
        {mod?.name && (
          <span style={{
            position: 'absolute',
            bottom: '4px',
            fontSize: '9px',
            color: '#666'
          }}>
            3D Model
          </span>
        )}
      </div>
    )
  }

  // Generic extra preview that switches based on type
  const ExtraPreview = ({ extraType, modifications, mod, compact = false }) => {
    const typeId = extraType?.id

    // Model types (gun, etc.)
    if (extraType?.type === 'model') {
      return <ModelPreview mod={mod} compact={compact} />
    }
    // Fox/Falco extras
    if (typeId === 'laser') {
      return <LaserBeamPreview modifications={modifications} compact={compact} />
    }
    if (typeId === 'sideb') {
      return <SideBPreview modifications={modifications} compact={compact} />
    }
    if (typeId === 'upb') {
      return <UpBPreview modifications={modifications} compact={compact} />
    }
    if (typeId === 'shine') {
      return <ShinePreview modifications={modifications} compact={compact} />
    }
    if (typeId === 'laser_ring') {
      return <LaserRingPreview modifications={modifications} compact={compact} />
    }
    // Sword trails
    if (typeId === 'sword') {
      return <SwordPreview modifications={modifications} compact={compact} />
    }
    // 2-color effects (punch, thunder, fireball, shadow ball)
    if (typeId === 'falcon_punch' || typeId === 'warlock_punch' ||
        typeId === 'thunder' || typeId === 'pk_thunder' ||
        typeId === 'fireball' || typeId === 'shadow_ball') {
      return <DualColorPreview extraType={extraType} modifications={modifications} compact={compact} />
    }
    // Fallback to laser for unknown types
    console.warn('[ExtraPreview] Unknown extra type:', typeId)
    return <LaserBeamPreview modifications={modifications} compact={compact} />
  }

  // Convert currentColors (object from API) to modifications format for preview
  const currentColorsToMods = (colors) => {
    if (!colors) return null
    const mods = {}
    for (const [key, value] of Object.entries(colors)) {
      mods[key] = { color: value }
    }
    return mods
  }

  // Extras mode UI
  if (extrasMode && selectedFighter) {
    const extraTypes = getExtraTypes(selectedFighter.name)
    console.log('[CharacterMode] Extras for', selectedFighter.name, ':', extraTypes.map(t => t.id))
    if (selectedExtraType) {
      console.log('[CharacterMode] Selected extra type:', selectedExtraType.id, selectedExtraType)
    }

    return (
      <div className="mex-content">
        <div className="fighters-list">
          <div className="extras-header">
            <h3>Extras</h3>
            <button
              className="btn-back-small"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('back'); setExtrasMode(false); setSelectedExtraType(null); setSelectedExtraMod(null); setCurrentColors(null); }}
            >
              ← Back
            </button>
          </div>
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
                    {extraType.shared && extraType.sharedWith && (
                      <span className="shared-note">
                        Applies to {extraType.owner} & {extraType.sharedWith.join(', ')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="costumes-panel">
          {selectedExtraType ? (
            <>
              {/* Currently in MEX section - shows actual colors from .dat (or model status) */}
              <div className="costumes-section">
                <h3>Currently in MEX</h3>
                <div className="costume-list existing">
                  {selectedExtraType.type === 'model' ? (
                    // Model type - just show a placeholder, no color preview
                    <div className="costume-card existing-costume">
                      <div className="costume-preview" style={{ padding: '8px' }}>
                        <ModelPreview mod={{ name: 'Current' }} compact />
                      </div>
                      <div className="costume-info">
                        <h4>Current Model</h4>
                        <span style={{ fontSize: '11px', color: '#888' }}>Select a model below to replace</span>
                      </div>
                    </div>
                  ) : (
                    // Color type - show current colors
                    <div className={`costume-card existing-costume ${isVanilla ? 'vanilla-extra' : ''}`}>
                      <div className="costume-preview" style={{ padding: '8px' }}>
                        {currentColors ? (
                          <ExtraPreview extraType={selectedExtraType} modifications={currentColorsToMods(currentColors)} compact />
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
                  )}
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
                        onMouseEnter={playHoverSound}
                        onClick={() => { playSound('start'); handleImportExtra(); }}
                        disabled={importingExtra}
                      >
                        {importingExtra ? 'Importing...' : 'Import Selected'}
                      </button>
                    )}
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
                        <ExtraPreview extraType={selectedExtraType} modifications={mod.modifications} mod={mod} compact />
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
                      <p>No extras in vault. Create some in Storage → {selectedFighter.name} → Extras.</p>
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
  // Hide non-playable characters
  const hiddenCharacters = ['Nana', 'Master Hand', 'Crazy Hand', 'Wireframe Male', 'Wireframe Female', 'Giga Bowser', 'Sandbag']
  const playableFighters = fighters.filter(f => !hiddenCharacters.includes(f.name))

  return (
    <div className="mex-content">
      <div className="fighters-list">
        <div className="fighters-header">
          <div className="mode-toggle">
            <button
              className={`mode-toggle-btn ${mode === 'characters' ? 'active' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={() => { if (mode !== 'characters') { playSound('boop'); onModeChange('characters'); } }}
            >
              Fighters
            </button>
            <button
              className={`mode-toggle-btn ${mode === 'stages' ? 'active' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={() => { if (mode !== 'stages') { playSound('boop'); onModeChange('stages'); } }}
            >
              Stages
            </button>
          </div>
          <span className="fighters-count">{playableFighters.length}</span>
        </div>
        <div className="fighter-items">
          {playableFighters.map(fighter => {
            const availableCostumes = getCostumesForFighter(fighter.name)
            return (
              <div
                key={fighter.internalId}
                className={`fighter-item ${selectedFighter?.internalId === fighter.internalId ? 'selected' : ''}`}
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('boop'); onSelectFighter(fighter); }}
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
              <div className="costumes-section-header">
                <h3>In ISO ({dataReady ? mexCostumes.length : 'Loading...'})</h3>
                <div className="team-color-tokens">
                  {[
                    { id: 'red', label: 'R', color: '#ff4757' },
                    { id: 'blue', label: 'B', color: '#3742fa' },
                    { id: 'green', label: 'G', color: '#2ed573' }
                  ].map(c => (
                    <div
                      key={c.id}
                      className={`team-color-token ${selectedTeamColor === c.id ? 'selected' : ''}`}
                      style={{ '--token-color': c.color }}
                      onClick={() => handleTeamColorClick(c.id)}
                      onMouseEnter={playHoverSound}
                      title={`${c.id.charAt(0).toUpperCase() + c.id.slice(1)} Team - click to assign`}
                    >
                      {c.label}
                    </div>
                  ))}
                </div>
              </div>
              <div className={`costume-list existing ${reordering ? 'processing' : ''} ${loadingFighter ? 'processing' : ''}`}>
                {mexCostumes.map((costume, idx) => {
                  const isDragging = draggedIndex === idx
                  const isDragOver = dragOverIndex === idx
                  const costumeTeamColors = getCostumeTeamColor(idx)
                  const isTeamAssignable = selectedTeamColor !== null
                  return (
                    <div
                      key={idx}
                      className={`costume-card existing-costume ${isDragging ? 'dragging' : ''} ${isDragOver ? 'drag-over' : ''} ${dataReady ? 'card-visible' : 'card-hidden'} ${isTeamAssignable ? 'team-assignable' : ''}`}
                      style={{ animationDelay: dataReady ? `${idx * 30}ms` : '0ms' }}
                      draggable={!removing && !reordering && !isTeamAssignable}
                      onMouseEnter={playHoverSound}
                      onClick={isTeamAssignable ? () => handleCostumeTeamAssign(idx) : undefined}
                      onDragStart={(e) => !isTeamAssignable && handleDragStart(e, idx)}
                      onDragOver={handleDragOver}
                      onDragEnter={(e) => handleDragEnter(e, idx)}
                      onDragLeave={handleDragLeave}
                      onDrop={(e) => handleDrop(e, idx)}
                      onDragEnd={handleDragEnd}
                    >
                      <div className="costume-preview">
                        {costume.cspUrl && (
                          <img
                            src={`${API_URL.replace('/api/mex', '')}${costume.cspUrl}`}
                            alt={costume.name}
                            onError={(e) => e.target.style.display = 'none'}
                          />
                        )}
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
                        {costume.iconUrl && (
                          <div className="stock-icon-overlay">
                            <img
                              src={`${API_URL.replace('/api/mex', '')}${costume.iconUrl}`}
                              alt="Stock"
                              onError={(e) => e.target.style.display = 'none'}
                            />
                          </div>
                        )}
                        {/* Team color badges */}
                        {costumeTeamColors.length > 0 && (
                          <div className="team-color-badges">
                            {costumeTeamColors.map(color => (
                              <div
                                key={color}
                                className={`team-color-badge team-${color}`}
                                title={`${color.charAt(0).toUpperCase() + color.slice(1)} Team`}
                              >
                                {color[0].toUpperCase()}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="costume-info">
                        <h4>{costume.name}</h4>
                      </div>
                    </div>
                  )
                })}
                {dataReady && mexCostumes.length === 0 && (
                  <div className="no-costumes">
                    <p>No costumes in MEX yet</p>
                  </div>
                )}
              </div>
              {reordering && (
                <div className="reorder-overlay">
                  <div className="reorder-spinner"></div>
                  <span>Reordering...</span>
                </div>
              )}
            </div>

            <div className="costumes-section">
              <div className="costumes-section-header">
                <h3>
                  Available to Import ({dataReady ? getCostumesForFighter(selectedFighter.name).length : 'Loading...'})
                  {selectedCostumes.size > 0 && ` - ${selectedCostumes.size} selected`}
                </h3>
                <div className="batch-controls">
                  {getCostumesForFighter(selectedFighter.name).length > 0 && (
                    <button
                      className="btn-select-all"
                      onMouseEnter={playHoverSound}
                      onClick={() => { playSound('boop'); selectAllCostumes(); }}
                      disabled={loadingFighter || batchImporting}
                    >
                      Select All
                    </button>
                  )}
                  {selectedCostumes.size > 0 && (
                    <>
                      <button
                        className="btn-batch-import"
                        onMouseEnter={playHoverSound}
                        onClick={() => { playSound('start'); handleBatchImport(); }}
                        disabled={batchImporting || loadingFighter}
                      >
                        {batchImporting
                          ? `Importing ${batchProgress.current}/${batchProgress.total}...`
                          : `Import All Selected (${selectedCostumes.size})`}
                      </button>
                      <button
                        className="btn-clear-selection"
                        onMouseEnter={playHoverSound}
                        onClick={() => { playSound('boop'); clearSelection(); }}
                        disabled={batchImporting || loadingFighter}
                      >
                        Clear
                      </button>
                    </>
                  )}
                  {hasExtras(selectedFighter.name) && (
                    <button
                      className="btn-extras-mode"
                      onMouseEnter={playHoverSound}
                      onClick={() => { playSound('boop'); setExtrasMode(true); }}
                    >
                      Extras
                    </button>
                  )}
                </div>
              </div>
              <div className={`costume-list ${loadingFighter ? 'processing' : ''}`} ref={availableListRef}>
                {getCostumesForFighter(selectedFighter.name).map((costume, idx) => {
                  const isSelected = selectedCostumes.has(costume.zipPath)
                  const cascadeDelay = (mexCostumes.length + idx) * 30
                  return (
                    <div
                      key={idx}
                      className={`costume-card ${isSelected ? 'selected' : ''} ${dataReady ? 'card-visible' : 'card-hidden'}`}
                      style={{ animationDelay: dataReady ? `${cascadeDelay}ms` : '0ms' }}
                      onMouseEnter={playHoverSound}
                      onClick={() => { if (!batchImporting && !loadingFighter) { playSound('boop'); toggleCostumeSelection(costume.zipPath); } }}
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
                        {costume.stockUrl && (
                          <div className="stock-icon-overlay">
                            <img
                              src={`${API_URL.replace('/api/mex', '')}${costume.stockUrl}`}
                              alt="Stock"
                              onError={(e) => e.target.style.display = 'none'}
                            />
                          </div>
                        )}
                        {costume.slippiSafe && (
                          <div className="slippi-badge slippi-badge-overlay" title="Slippi Safe">
                            ✓
                          </div>
                        )}
                      </div>
                      <div className="costume-info">
                        <h4>{costume.name?.includes(' - ') ? costume.name.split(' - ').slice(1).join(' - ') : costume.name}</h4>
                      </div>
                    </div>
                  )
                })}
                {dataReady && getCostumesForFighter(selectedFighter.name).length === 0 && (
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

      <ConfirmDialog
        show={showConfirmDialog}
        title="Remove Costume"
        message={pendingRemoval
          ? (pendingRemoval.isIceClimbers
              ? `Are you sure you want to remove "${pendingRemoval.costumeName}" (and paired Nana) from Ice Climbers?`
              : `Are you sure you want to remove "${pendingRemoval.costumeName}" from ${pendingRemoval.fighterName}?`)
          : ''}
        confirmText="Remove"
        onConfirm={confirmRemoveCostume}
        onCancel={() => { setShowConfirmDialog(false); setPendingRemoval(null); }}
      />
    </div>
  )
}
