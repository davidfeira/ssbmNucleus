/**
 * useCustomStages - custom stage vault/project state and logic for StageMode
 *
 * Covers: vault + in-project custom stage fetching, batch selection,
 * batch install (with auto SSS grid layout), and removal from project.
 */
import { useState, useEffect } from 'react'

export default function useCustomStages({ API_URL, onRefresh }) {
  const [vaultStages, setVaultStages] = useState([])
  const [projectCustomStages, setProjectCustomStages] = useState([])
  const [addingStage, setAddingStage] = useState(null)
  const [selectedCustomStages, setSelectedCustomStages] = useState(new Set())
  const [batchInstallingStages, setBatchInstallingStages] = useState(false)
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
    setSelectedCustomStages(new Set(vaultStages.map(s => s.slug)))
  }

  const clearCustomStageSelection = () => {
    setSelectedCustomStages(new Set())
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
    for (let i = 0; i < slugs.length; i++) {
      setBatchStageProgress({ current: i + 1, total: slugs.length })
      try {
        const response = await fetch(`${API_URL}/custom-stages/install`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slug: slugs[i] })
        })
        const data = await response.json()
        if (!data.success) {
          console.error(`Failed to install ${slugs[i]}:`, data.error)
        }
      } catch (err) {
        console.error(`Error installing ${slugs[i]}:`, err)
      }
    }
    await autoApplySssGrid()
    setBatchInstallingStages(false)
    setSelectedCustomStages(new Set())
    await fetchCustomStagesData()
    onRefresh()
  }

  const handleRemoveCustomStage = async (stageName) => {
    if (!confirm(`Remove "${stageName}" from the project?`)) return
    try {
      const response = await fetch(`${API_URL}/custom-stages/remove-from-project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: stageName })
      })
      const data = await response.json()
      if (data.success) {
        await fetchCustomStagesData()
        onRefresh()
      } else {
        alert(data.error || 'Failed to remove stage')
      }
    } catch (err) {
      alert(`Error: ${err.message}`)
    }
  }

  return {
    vaultStages,
    projectCustomStages,
    addingStage,
    setAddingStage,
    selectedCustomStages,
    batchInstallingStages,
    batchStageProgress,
    fetchCustomStagesData,
    toggleCustomStageSelection,
    selectAllCustomStages,
    clearCustomStageSelection,
    handleBatchInstallStages,
    handleRemoveCustomStage
  }
}
