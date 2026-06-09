/**
 * useCostumes - MEX costume management state and logic for CharacterMode
 *
 * Covers: MEX costume fetching, team colors, single/batch import,
 * removal (with Ice Climbers Popo/Nana pairing), drag-drop reordering,
 * and available-costume selection.
 */
import { useState, useEffect, useRef } from 'react'
import { playSound } from '../../../utils/sounds'

export default function useCostumes({ API_URL, fighters, storageCostumes, selectedFighter, onRefresh }) {
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
    let completedCount = 0
    const importedNanas = new Set()
    const markBatchStepComplete = () => {
      completedCount += 1
      setBatchProgress({ current: completedCount, total })
    }

    for (let i = 0; i < costumesToImport.length; i++) {
      const zipPath = costumesToImport[i]
      const costume = storageCostumes.find(c => c.zipPath === zipPath)

      if (!costume) {
        failCount++
        markBatchStepComplete()
        continue
      }

      // Skip if this is a Nana that was already imported as part of a Popo pair
      if (importedNanas.has(zipPath)) {
        markBatchStepComplete()
        continue
      }

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
      } finally {
        markBatchStepComplete()
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

  return {
    mexCostumes,
    loadingFighter,
    dataReady,
    importing,
    importingCostume,
    removing,
    removingCostume,
    selectedCostumes,
    batchImporting,
    batchProgress,
    draggedIndex,
    dragOverIndex,
    reordering,
    showConfirmDialog,
    setShowConfirmDialog,
    pendingRemoval,
    setPendingRemoval,
    teamColors,
    selectedTeamColor,
    availableListRef,
    handleTeamColorClick,
    handleCostumeTeamAssign,
    getCostumeTeamColor,
    handleImportCostume,
    handleRemoveCostume,
    confirmRemoveCostume,
    handleBatchImport,
    handleDragStart,
    handleDragOver,
    handleDragEnter,
    handleDragLeave,
    handleDrop,
    handleDragEnd,
    getCostumesForFighter,
    toggleCostumeSelection,
    selectAllCostumes,
    clearSelection
  }
}
