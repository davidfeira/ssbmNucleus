/**
 * useCostumes - MEX costume management state and logic for CharacterMode
 *
 * Covers: MEX costume fetching, team colors, single/batch import,
 * removal (with Ice Climbers Popo/Nana pairing), drag-drop reordering,
 * and available-costume selection.
 */
import { useState, useEffect, useRef } from 'react'
import { playSound } from '../../../utils/sounds'

// Zelda and Sheik are one in-game pairing: slot N of one loads slot N of the
// other on transform. The panel therefore shows BOTH fighters together (Zelda
// on top, Sheik below, slot-paired) whenever either is selected.
export const ZS_PAIR = ['Zelda', 'Sheik']
export const isZeldaSheikName = (name) => ZS_PAIR.includes(name)

const EMPTY_TEAM = { red: null, blue: null, green: null }

export default function useCostumes({ API_URL, fighters, storageCostumes, selectedFighter, onRefresh }) {
  const [mexCostumes, setMexCostumes] = useState([])
  const [loadingFighter, setLoadingFighter] = useState(false)
  const [dataReady, setDataReady] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importingCostume, setImportingCostume] = useState(null)
  const [removing, setRemoving] = useState(false)
  const [removingCostume, setRemovingCostume] = useState(null)
  const [selectedCostumes, setSelectedCostumes] = useState(new Set())
  const [selectedInstalledCostumes, setSelectedInstalledCostumes] = useState(new Set())
  const [batchImporting, setBatchImporting] = useState(false)
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 })
  const [draggedIndex, setDraggedIndex] = useState(null)
  const [dragOverIndex, setDragOverIndex] = useState(null)
  const [reordering, setReordering] = useState(false)

  // Zelda/Sheik combined view: both fighters' MEX costumes + team colors
  const [pairCostumes, setPairCostumes] = useState({ Zelda: [], Sheik: [] })
  const [pairTeamColors, setPairTeamColors] = useState({ Zelda: EMPTY_TEAM, Sheik: EMPTY_TEAM })
  const [draggedRow, setDraggedRow] = useState(null) // which ZS row a drag started in
  const isZeldaSheik = !!selectedFighter && isZeldaSheikName(selectedFighter.name)

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
      if (isZeldaSheikName(selectedFighter.name)) {
        setPairCostumes({ Zelda: [], Sheik: [] })
        fetchPair(true)
      } else {
        fetchMexCostumes(selectedFighter.name, true)
        fetchTeamColors(selectedFighter.name)
      }
      // Reset scroll position of Available to Import list
      if (availableListRef.current) {
        availableListRef.current.scrollTop = 0
      }
    }
  }, [selectedFighter])

  // Fetch BOTH Zelda and Sheik costume lists + team colors for the combined view.
  const fetchPair = async (showLoading = false) => {
    if (showLoading) {
      setLoadingFighter(true)
    }
    try {
      const fetchOne = async (name, path, fallback) => {
        try {
          const r = await fetch(`${API_URL}/fighters/${encodeURIComponent(name)}/${path}`)
          const d = await r.json()
          if (!d.success) {
            console.error(`Failed to fetch ${name} ${path}:`, d.error)
            return fallback
          }
          return d
        } catch (err) {
          console.error(`Failed to fetch ${name} ${path}:`, err)
          return fallback
        }
      }
      // The costumes endpoint shells out to MexCLI, which opens the whole
      // workspace -- two CONCURRENT mexcli processes on the same project make
      // one of them fail (and that fighter shows 0 costumes). Fetch the two
      // costume lists SEQUENTIALLY; team colors are plain file reads, so those
      // can run in parallel.
      const zc = await fetchOne('Zelda', 'costumes', {})
      const sc = await fetchOne('Sheik', 'costumes', {})
      const [zt, st] = await Promise.all([
        fetchOne('Zelda', 'team-colors', EMPTY_TEAM),
        fetchOne('Sheik', 'team-colors', EMPTY_TEAM)
      ])
      setPairCostumes({ Zelda: zc.costumes || [], Sheik: sc.costumes || [] })
      setPairTeamColors({
        Zelda: { red: zt.red ?? null, blue: zt.blue ?? null, green: zt.green ?? null },
        Sheik: { red: st.red ?? null, blue: st.blue ?? null, green: st.green ?? null }
      })
    } catch (err) {
      console.error('Failed to fetch Zelda/Sheik pair:', err)
      setPairCostumes({ Zelda: [], Sheik: [] })
    } finally {
      if (showLoading) {
        setLoadingFighter(false)
        setTimeout(() => setDataReady(true), 50)
      }
    }
  }

  // Refresh the In-ISO list(s) after an import/remove/reorder, pair-aware.
  const refreshMexCostumes = async (fighterName) => {
    if (isZeldaSheikName(fighterName)) {
      await fetchPair()
    } else {
      await fetchMexCostumes(fighterName)
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

  // Pair-view variants: team colors are PER FIGHTER, so the combined view
  // assigns/reads against whichever row (Zelda or Sheik) the tile lives in.
  const getPairCostumeTeamColor = (fighterName, costumeIndex) => {
    const tc = pairTeamColors[fighterName] || EMPTY_TEAM
    const colors = []
    if (tc.red === costumeIndex) colors.push('red')
    if (tc.blue === costumeIndex) colors.push('blue')
    if (tc.green === costumeIndex) colors.push('green')
    return colors
  }

  const handlePairCostumeTeamAssign = async (fighterName, costumeIndex) => {
    if (!selectedTeamColor) return
    try {
      const response = await fetch(`${API_URL}/fighters/${encodeURIComponent(fighterName)}/team-colors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ color: selectedTeamColor, costumeIndex })
      })
      const data = await response.json()
      if (data.success) {
        playSound('newSkin')
        await fetchPair()
        setSelectedTeamColor(null)
      } else {
        console.error('Failed to set team color:', data.error)
      }
    } catch (err) {
      console.error('Failed to set team color:', err)
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
      // Custom-character added skin: route through the dedicated MexCLI
      // import-costume path instead of the vanilla /import endpoint
      if (costume.isCustomCharSkin) {
        const response = await fetch(`${API_URL}/custom-characters/install-skin`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            slug: costume.customSlug,
            skinId: costume.skinId,
            fighterName: costume.character,
          })
        })
        const data = await response.json()
        if (data.success) {
          await onRefresh()
          await refreshMexCostumes(costume.character)
        } else {
          alert(`Import failed: ${data.error}`)
        }
        return
      }

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
          await refreshMexCostumes(costume.character)
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

  const removeCostumeFromProject = async (fighterName, costumeIndex) => {
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
      throw new Error(data.error || 'Remove failed')
    }

    return data
  }

  const handleBatchRemoveCostumes = () => {
    if (removing || selectedInstalledCostumes.size === 0) return

    const items = Array.from(selectedInstalledCostumes)
      .map(parseInstalledCostumeKey)
      .filter(Boolean)

    if (items.length === 0) return

    setPendingRemoval({ bulk: true, items })
    setShowConfirmDialog(true)
  }

  const confirmRemoveCostume = async () => {
    if (!pendingRemoval) return

    const removal = pendingRemoval
    setShowConfirmDialog(false)
    setPendingRemoval(null)

    if (removal.bulk) {
      await confirmBatchRemoveCostumes(removal.items)
      return
    }

    const { fighterName, costumeIndex, costumeName, isIceClimbers } = removal

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
      await removeCostumeFromProject(fighterName, costumeIndex)

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
      await refreshMexCostumes(fighterName)
      setSelectedInstalledCostumes(prev => {
        const next = new Set(prev)
        next.delete(installedCostumeKey(fighterName, costumeIndex))
        return next
      })

    } catch (err) {
      console.error('Remove error:', err)
      alert(`Remove error: ${err.message}`)
    } finally {
      setRemoving(false)
      setRemovingCostume(null)
    }
  }

  const confirmBatchRemoveCostumes = async (items) => {
    const deduped = new Map()
    items.forEach(item => {
      deduped.set(installedCostumeKey(item.fighterName, item.costumeIndex), item)
      if (item.fighterName === 'Ice Climbers') {
        const nanaFighter = fighters.find(f => f.internalId === 11)
        if (nanaFighter) {
          deduped.set(installedCostumeKey(nanaFighter.name, item.costumeIndex), {
            fighterName: nanaFighter.name,
            costumeIndex: item.costumeIndex,
            costumeName: `Paired Nana slot ${item.costumeIndex + 1}`,
          })
        }
      }
    })

    const removalQueue = Array.from(deduped.values()).sort((a, b) => {
      const fighterCompare = a.fighterName.localeCompare(b.fighterName)
      return fighterCompare || b.costumeIndex - a.costumeIndex
    })

    setRemoving(true)
    let successCount = 0
    let failCount = 0

    // ONE batch call: the backend removes every selected costume in a single
    // workspace recompile (descending index per fighter, so indices stay valid) --
    // ~Nx faster than /remove per costume, same final costume set.
    try {
      const items = removalQueue.map(it => ({
        fighter: it.fighterName, costumeIndex: it.costumeIndex
      }))
      const response = await fetch(`${API_URL}/remove-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items })
      })
      const data = await response.json()
      if (data.success) {
        successCount = items.length
      } else {
        failCount = items.length
        console.error('Batch remove failed:', data.error)
      }
    } catch (err) {
      failCount = removalQueue.length
      console.error('Batch remove error:', err)
    }

    try {
      await onRefresh()
      if (selectedFighter) {
        await refreshMexCostumes(selectedFighter.name)
      }
    } finally {
      setRemoving(false)
      setRemovingCostume(null)
      setSelectedInstalledCostumes(new Set())
    }

    if (failCount > 0) {
      playSound('error')
      alert(`Batch remove completed:\n${successCount} removed, ${failCount} failed`)
    } else {
      playSound('boop')
      console.log(`âœ“ Successfully removed ${successCount} costume(s)`)
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
    const markBatchStepComplete = (n = 1) => {
      completedCount += n
      setBatchProgress({ current: completedCount, total })
    }

    // Partition the selection: ordinary costumes (incl. Ice Climbers pairs)
    // collapse into ONE /import-batch call (one workspace recompile + parallel
    // CSP decode -- ~7x faster than N /import calls). Custom-character skins use
    // a different endpoint (/custom-characters/install-skin) and aren't a plain
    // costume zip, so they stay individual.
    const batchItems = []        // { fighter, costumePath } in selection order
    const batchSelections = []   // selected zipPaths represented in batchItems
    const customSkins = []       // costumes needing install-skin

    for (const zipPath of costumesToImport) {
      const costume = storageCostumes.find(c => c.zipPath === zipPath)

      if (!costume) {
        failCount++
        markBatchStepComplete()
        continue
      }

      // Skip if this is a Nana that was already queued as part of a Popo pair
      if (importedNanas.has(zipPath)) {
        markBatchStepComplete()
        continue
      }

      if (costume.isCustomCharSkin) {
        customSkins.push(costume)
        continue
      }

      // Ice Climbers: queue the paired Nana alongside Popo. Two separate manifest
      // entries (Ice Climbers + Nana fighter) -- NOT one bundled zip -- keeps the
      // Popo/Nana slots aligned, same as two sequential /import calls.
      if (costume.isPopo && costume.pairedNanaId) {
        const nanaCostume = storageCostumes.find(c => c.folder === costume.pairedNanaId)
        const nanaFighter = fighters.find(f => f.internalId === 11)

        if (!nanaCostume) {
          console.error('Paired Nana costume not found:', costume.pairedNanaId)
          failCount++
          markBatchStepComplete()
          continue
        }
        if (!nanaFighter) {
          console.error('Nana fighter (ID 11) not found in project')
          failCount++
          markBatchStepComplete()
          continue
        }

        batchItems.push({ fighter: 'Ice Climbers', costumePath: costume.zipPath })
        batchItems.push({ fighter: nanaFighter.name, costumePath: nanaCostume.zipPath })
        importedNanas.add(nanaCostume.zipPath)
        batchSelections.push(zipPath)
      } else {
        batchItems.push({ fighter: costume.character, costumePath: costume.zipPath })
        batchSelections.push(zipPath)
      }
    }

    // 1) Custom-character skins -- sequential (separate endpoint, not batchable).
    for (const costume of customSkins) {
      try {
        const response = await fetch(`${API_URL}/custom-characters/install-skin`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            slug: costume.customSlug,
            skinId: costume.skinId,
            fighterName: costume.character,
          })
        })
        const data = await response.json()
        if (data.success) {
          successCount++
        } else {
          console.error(`Import failed for ${costume.name}:`, data.error)
          failCount++
        }
      } catch (err) {
        console.error(`Import error for ${costume.name}:`, err)
        failCount++
      } finally {
        markBatchStepComplete()
      }
    }

    // 2) Everything else -- ONE batch call.
    if (batchItems.length > 0) {
      try {
        const response = await fetch(`${API_URL}/import-batch`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items: batchItems })
        })
        const data = await response.json()
        if (data.success) {
          console.log(`✓ Batch-imported ${batchItems.length} file(s) for ${batchSelections.length} selection(s)`, data.result)
          successCount += batchSelections.length
        } else {
          console.error('Batch import failed:', data.error)
          failCount += batchSelections.length
        }
      } catch (err) {
        console.error('Batch import error:', err)
        failCount += batchSelections.length
      } finally {
        markBatchStepComplete(batchSelections.length)
      }
    }

    // Refresh once at the end
    await onRefresh()
    if (selectedFighter) {
      await refreshMexCostumes(selectedFighter.name)
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
    setDraggedRow(null)
  }

  // Pair-view drag/drop: reorder WITHIN one row (Zelda or Sheik) only --
  // cross-row drops are ignored so a Zelda costume can't land in Sheik's list.
  const handlePairDragStart = (e, fighterName, index) => {
    setDraggedRow(fighterName)
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handlePairDragEnter = (e, fighterName, index) => {
    e.preventDefault()
    setDragOverIndex(fighterName === draggedRow ? index : null)
  }

  const handlePairDrop = async (e, fighterName, toIndex) => {
    e.preventDefault()
    const fromIndex = draggedIndex
    const sameRow = draggedRow === fighterName
    setDraggedIndex(null)
    setDragOverIndex(null)
    setDraggedRow(null)
    if (!sameRow || fromIndex === null || fromIndex === toIndex || reordering) {
      return
    }

    // Optimistically reorder the row
    setPairCostumes(prev => {
      const row = [...(prev[fighterName] || [])]
      const [moved] = row.splice(fromIndex, 1)
      row.splice(toIndex, 0, moved)
      return { ...prev, [fighterName]: row }
    })

    setReordering(true)
    try {
      const response = await fetch(`${API_URL}/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fighter: fighterName, fromIndex, toIndex })
      })
      const data = await response.json()
      if (data.success) {
        console.log(`✓ Reordered ${fighterName} costume from ${fromIndex} to ${toIndex}`)
        playSound('boop')
      } else {
        alert(`Reorder failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Reorder error:', err)
      alert(`Reorder error: ${err.message}`)
    } finally {
      await fetchPair()
      setReordering(false)
    }
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
    const names = isZeldaSheik ? ZS_PAIR : [selectedFighter.name]
    setSelectedCostumes(prev => {
      const newSet = new Set(prev)
      names.forEach(name => getCostumesForFighter(name).forEach(c => newSet.add(c.zipPath)))
      return newSet
    })
  }

  const clearSelection = () => {
    setSelectedCostumes(new Set())
  }

  const installedCostumeKey = (fighterName, costumeIndex) => JSON.stringify([fighterName, costumeIndex])

  const parseInstalledCostumeKey = (key) => {
    try {
      const [fighterName, costumeIndex] = JSON.parse(key)
      if (typeof fighterName !== 'string' || !Number.isInteger(costumeIndex)) return null
      return { fighterName, costumeIndex }
    } catch (err) {
      console.error('Invalid installed costume key:', key, err)
      return null
    }
  }

  const toggleInstalledCostumeSelection = (fighterName, costumeIndex) => {
    const key = installedCostumeKey(fighterName, costumeIndex)
    setSelectedInstalledCostumes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(key)) {
        newSet.delete(key)
      } else {
        newSet.add(key)
      }
      return newSet
    })
  }

  const clearInstalledCostumeSelection = () => {
    setSelectedInstalledCostumes(new Set())
  }

  return {
    mexCostumes,
    refreshMexCostumes,
    loadingFighter,
    dataReady,
    importing,
    importingCostume,
    removing,
    removingCostume,
    selectedCostumes,
    selectedInstalledCostumes,
    batchImporting,
    batchProgress,
    draggedIndex,
    dragOverIndex,
    reordering,
    isZeldaSheik,
    pairCostumes,
    draggedRow,
    getPairCostumeTeamColor,
    handlePairCostumeTeamAssign,
    handlePairDragStart,
    handlePairDragEnter,
    handlePairDrop,
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
    handleBatchRemoveCostumes,
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
    clearSelection,
    installedCostumeKey,
    toggleInstalledCostumeSelection,
    clearInstalledCostumeSelection
  }
}
