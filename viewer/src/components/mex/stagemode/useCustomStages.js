/**
 * useCustomStages - custom stage vault/project state and logic for StageMode
 *
 * Covers: vault + in-project custom stage fetching, batch selection,
 * batch install (with auto SSS grid layout), and removal from project.
 */
import { useState, useEffect } from 'react'
import { io } from 'socket.io-client'
import { appConfirm } from '../../../utils/appDialogs'
import { BACKEND_URL } from '../../../config'

export default function useCustomStages({ API_URL, onRefresh }) {
  const [vaultStages, setVaultStages] = useState([])
  const [projectCustomStages, setProjectCustomStages] = useState([])
  const [addingStage, setAddingStage] = useState(null)
  const [selectedCustomStages, setSelectedCustomStages] = useState(new Set())
  const [selectedInstalledCustomStages, setSelectedInstalledCustomStages] = useState(new Set())
  const [batchInstallingStages, setBatchInstallingStages] = useState(false)
  const [removingCustomStages, setRemovingCustomStages] = useState(false)
  const [batchStageProgress, setBatchStageProgress] = useState({ current: 0, total: 0 })

  useEffect(() => {
    fetchCustomStagesData()
  }, [])

  const fetchCustomStagesData = async () => {
    try {
      const [vaultRes, projectRes] = await Promise.all([
        fetch(`${API_URL}/custom-stages/list`),
        fetch(`${API_URL}/custom-stages/in-project`)
      ])
      const vaultData = await vaultRes.json()
      const projectData = await projectRes.json()
      if (vaultData.success) setVaultStages(vaultData.stages || [])
      if (projectData.success) setProjectCustomStages(projectData.stages || [])
    } catch (err) {
      console.error('Failed to fetch custom stages:', err)
    }
  }

  const toggleCustomStageSelection = (slug) => {
    setSelectedCustomStages(prev => {
      const next = new Set(prev)
      if (next.has(slug)) next.delete(slug)
      else next.add(slug)
      return next
    })
  }

  const selectAllCustomStages = () => {
    setSelectedCustomStages(prev => {
      const next = new Set(prev)
      vaultStages.forEach(stage => next.add(stage.slug))
      return next
    })
  }

  const clearCustomStageSelection = () => {
    setSelectedCustomStages(new Set())
  }

  const toggleInstalledCustomStageSelection = (stageName) => {
    setSelectedInstalledCustomStages(prev => {
      const next = new Set(prev)
      if (next.has(stageName)) next.delete(stageName)
      else next.add(stageName)
      return next
    })
  }

  const selectAllInstalledCustomStages = () => {
    setSelectedInstalledCustomStages(prev => {
      const next = new Set(prev)
      projectCustomStages.forEach(stage => next.add(stage.name))
      return next
    })
  }

  const clearInstalledCustomStageSelection = () => {
    setSelectedInstalledCustomStages(new Set())
  }

  const autoApplySssGrid = async () => {
    try {
      const res = await fetch(`${API_URL}/menus/sss/layout`)
      const data = await res.json()
      if (!data.success || !data.pages) return
      // Apply grid to each page that has icons
      const cols = 6
      const baseW = 5.95, baseH = 5.21, spacingX = 0.8, spacingY = 0.6, centerX = 0, centerY = 5.5
      const updatedPages = data.pages.map((page, pageIdx) => {
        if (pageIdx === 0) return page // leave vanilla page untouched
        const icons = page.icons || []
        if (icons.length === 0) return page
        const rows = Math.ceil(icons.length / cols)
        const sx = 1.0, sy = 1.0
        const iw = baseW + spacingX, ih = baseH + spacingY
        const totalW = Math.min(icons.length, cols) * iw - spacingX, totalH = rows * ih - spacingY
        const gridIcons = icons.map((icon, i) => {
          const col = i % cols, row = Math.floor(i / cols)
          return { ...icon, x: centerX - totalW / 2 + iw * col + baseW / 2, y: centerY + totalH / 2 - ih * row - baseH / 2, z: 0, scaleX: sx, scaleY: sy }
        })
        return { ...page, icons: gridIcons }
      })
      await fetch(`${API_URL}/menus/sss/layout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pages: updatedPages })
      })
    } catch (err) {
      console.error('Auto SSS grid failed:', err)
    }
  }

  const handleBatchInstallStages = async () => {
    const slugs = [...selectedCustomStages]
    if (slugs.length === 0) return
    setBatchInstallingStages(true)
    setBatchStageProgress({ current: 0, total: slugs.length })
    // Live progress via SocketIO so the bar moves instead of sitting at 0/N
    // (single synchronous request otherwise).
    const socket = io(BACKEND_URL)
    socket.on('custom_stage_install_progress', (d) => {
      setBatchStageProgress({
        current: d.current ?? 0,
        total: d.total ?? slugs.length,
        message: d.message || null,
        name: d.name || null,
      })
    })
    // ONE batch call: the backend folds add-stage + per-track add-music +
    // set-stage-playlist for every selected stage into a single workspace recompile
    // (~Nx faster than /install per stage). Output is byte-identical to the per-stage
    // path.
    try {
      const response = await fetch(`${API_URL}/custom-stages/install-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slugs })
      })
      const data = await response.json()
      if (!data.success) {
        console.error('Batch stage install failed:', data.error)
        alert(data.error || 'Failed to add stages')
      } else {
        if (data.failed?.length) console.warn('Some stages failed to install:', data.failed)
        if (data.warnings?.length) console.warn('Install warnings:', data.warnings)
        setBatchStageProgress({ current: slugs.length, total: slugs.length })
      }
    } catch (err) {
      console.error('Batch stage install error:', err)
      alert(`Error: ${err.message}`)
    } finally {
      socket.disconnect()
    }
    // Re-fit the SSS grid to the new roster (places the new stages on the
    // stage-select grid), same step the per-stage path ran.
    await autoApplySssGrid()
    setBatchInstallingStages(false)
    setSelectedCustomStages(new Set())
    await fetchCustomStagesData()
    onRefresh()
  }

  const removeCustomStageFromProject = async (stageName) => {
    const response = await fetch(`${API_URL}/custom-stages/remove-from-project`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: stageName })
    })
    const data = await response.json()
    if (!data.success) {
      throw new Error(data.error || 'Failed to remove stage')
    }
    return data
  }

  const handleRemoveCustomStage = async (stageName) => {
    if (!await appConfirm(`Remove "${stageName}" from the project?`, {
      title: 'Remove Custom Stage',
      confirmText: 'Remove',
    })) return
    try {
      await removeCustomStageFromProject(stageName)
      setSelectedInstalledCustomStages(prev => {
        const next = new Set(prev)
        next.delete(stageName)
        return next
      })
      await fetchCustomStagesData()
      onRefresh()
    } catch (err) {
      alert(`Error: ${err.message}`)
    }
  }

  const handleBatchRemoveCustomStages = async () => {
    const names = [...selectedInstalledCustomStages]
    if (names.length === 0 || removingCustomStages) return
    if (!await appConfirm(`Remove ${names.length} selected custom stage(s) from the project?`, {
      title: 'Remove Selected Stages',
      confirmText: 'Remove',
    })) return

    setRemovingCustomStages(true)
    let successCount = 0
    let failCount = 0

    // ONE batch call: removes every selected stage in a single workspace recompile
    // (~Nx faster than /remove-from-project per stage, same final stage set).
    try {
      const response = await fetch(`${API_URL}/custom-stages/remove-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ names })
      })
      const data = await response.json()
      if (data.success) {
        successCount = data.totalRemoved ?? names.length
        failCount = data.totalFailed ?? 0
      } else {
        failCount = names.length
        console.error('Batch stage remove failed:', data.error)
      }
    } catch (err) {
      failCount = names.length
      console.error('Batch stage remove error:', err)
    }

    setRemovingCustomStages(false)
    setSelectedInstalledCustomStages(new Set())
    await fetchCustomStagesData()
    onRefresh()

    if (failCount > 0) {
      alert(`Batch remove completed:\n${successCount} removed, ${failCount} failed`)
    }
  }

  return {
    vaultStages,
    projectCustomStages,
    addingStage,
    setAddingStage,
    selectedCustomStages,
    selectedInstalledCustomStages,
    batchInstallingStages,
    removingCustomStages,
    batchStageProgress,
    fetchCustomStagesData,
    toggleCustomStageSelection,
    selectAllCustomStages,
    clearCustomStageSelection,
    toggleInstalledCustomStageSelection,
    selectAllInstalledCustomStages,
    clearInstalledCustomStageSelection,
    handleBatchInstallStages,
    handleRemoveCustomStage,
    handleBatchRemoveCustomStages
  }
}
