/**
 * useCustomCharacters - add-character modal state and custom fighter
 * install/remove logic for CharacterMode.
 */
import { useState } from 'react'

export default function useCustomCharacters({ API_URL, onRefresh }) {
  // Add character modal state
  const [showAddCharacterModal, setShowAddCharacterModal] = useState(false)
  const [vaultCharacters, setVaultCharacters] = useState([])
  const [addingCharacter, setAddingCharacter] = useState(null)
  const [selectedVaultChars, setSelectedVaultChars] = useState(new Set())
  const [batchAddingChars, setBatchAddingChars] = useState(false)
  const [batchCharProgress, setBatchCharProgress] = useState({ current: 0, total: 0 })

  const [removingFighter, setRemovingFighter] = useState(false)
  const [removingFighterName, setRemovingFighterName] = useState('')

  const openAddCharacterModal = async () => {
    setShowAddCharacterModal(true)
    try {
      const response = await fetch(`${API_URL}/custom-characters/list`)
      const data = await response.json()
      if (data.success) setVaultCharacters(data.characters || [])
    } catch (err) {
      console.error('Failed to fetch vault characters:', err)
    }
  }

  const toggleVaultCharSelection = (slug) => {
    setSelectedVaultChars(prev => {
      const next = new Set(prev)
      if (next.has(slug)) next.delete(slug)
      else next.add(slug)
      return next
    })
  }

  const autoApplyCssGrid = async () => {
    try {
      const res = await fetch(`${API_URL}/menus/css/layout`)
      const data = await res.json()
      if (!data.success) return
      const { icons, template } = data
      if (!icons || !template || icons.length === 0) return
      const cols = template.iconsPerRow || 9
      const rows = Math.ceil(icons.length / cols)
      const vanillaW = 63.45, vanillaH = 21.6, baseW = 7.05, baseH = 7.2
      const sx = vanillaW / (cols * baseW), sy = vanillaH / (rows * baseH)
      const newTemplate = { ...template, scaleX: sx, scaleY: sy, iconWidth: baseW, iconHeight: baseH, centerX: 0.05, centerY: 9.5 }
      const iw = baseW * sx, ih = baseH * sy
      const totalW = Math.min(icons.length, cols) * iw, totalH = rows * ih
      const gridIcons = icons.map((icon, i) => {
        const col = i % cols, row = Math.floor(i / cols)
        return { ...icon, x: newTemplate.centerX - totalW / 2 + iw * col + iw / 2, y: newTemplate.centerY + totalH / 2 - ih * row - ih / 2, z: 0, scaleX: sx, scaleY: sy, collisionSizeX: baseW, collisionSizeY: baseH, collisionOffsetX: 0, collisionOffsetY: 0 }
      })
      await fetch(`${API_URL}/menus/css/layout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ icons: gridIcons, template: newTemplate })
      })
    } catch (err) {
      console.error('Auto CSS grid failed:', err)
    }
  }

  const handleBatchAddCharacters = async () => {
    const slugs = [...selectedVaultChars]
    if (slugs.length === 0) return
    setBatchAddingChars(true)
    setBatchCharProgress({ current: 0, total: slugs.length })
    for (let i = 0; i < slugs.length; i++) {
      setBatchCharProgress({ current: i + 1, total: slugs.length })
      try {
        const response = await fetch(`${API_URL}/custom-characters/install`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ slug: slugs[i] })
        })
        const data = await response.json()
        if (!data.success) console.error(`Failed to install ${slugs[i]}:`, data.error)
      } catch (err) {
        console.error(`Error installing ${slugs[i]}:`, err)
      }
    }
    await autoApplyCssGrid()
    setBatchAddingChars(false)
    setSelectedVaultChars(new Set())
    setShowAddCharacterModal(false)
    onRefresh()
  }

  const handleRemoveFighter = async (fighterName) => {
    if (!confirm(`Remove "${fighterName}" from the project?`)) return
    setRemovingFighter(true)
    setRemovingFighterName(fighterName)
    try {
      const response = await fetch(`${API_URL}/custom-characters/remove-from-project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: fighterName })
      })
      const data = await response.json()
      if (data.success) {
        onRefresh()
      } else {
        alert(data.error || 'Failed to remove fighter')
      }
    } catch (err) {
      alert(`Error: ${err.message}`)
    } finally {
      setRemovingFighter(false)
      setRemovingFighterName('')
    }
  }

  return {
    showAddCharacterModal,
    setShowAddCharacterModal,
    vaultCharacters,
    addingCharacter,
    setAddingCharacter,
    selectedVaultChars,
    setSelectedVaultChars,
    batchAddingChars,
    batchCharProgress,
    removingFighter,
    removingFighterName,
    openAddCharacterModal,
    toggleVaultCharSelection,
    handleBatchAddCharacters,
    handleRemoveFighter
  }
}
