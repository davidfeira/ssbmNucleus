/**
 * useCustomCharacters - add-character modal state and custom fighter
 * install/remove logic for CharacterMode.
 */
import { useState } from 'react'
import { computeAutoCssLayout } from '../../../utils/cssGridLayout'
import { appConfirm } from '../../../utils/appDialogs'

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

  // Re-fit the character select grid to the new roster: auto-pick
  // columns/rows for the icon count and re-center every row (the old inline
  // version kept the column count fixed and left partial rows off-center).
  const autoApplyCssGrid = async () => {
    try {
      const res = await fetch(`${API_URL}/menus/css/layout`)
      const data = await res.json()
      if (!data.success) return
      const { icons, template } = data
      if (!icons || !template || icons.length === 0) return
      await fetch(`${API_URL}/menus/css/layout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(computeAutoCssLayout(icons, template))
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
    // ONE batch call: the backend folds add-fighter + victory + announcer for every
    // selected character into a single workspace recompile (~Nx faster than calling
    // /install per char, which re-recompiled ~4x each).
    try {
      const response = await fetch(`${API_URL}/custom-characters/install-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slugs })
      })
      const data = await response.json()
      if (!data.success) {
        console.error('Batch character install failed:', data.error)
        alert(data.error || 'Failed to add characters')
      } else {
        if (data.failed?.length) console.warn('Some characters failed to install:', data.failed)
        if (data.warnings?.length) console.warn('Install warnings:', data.warnings)
        setBatchCharProgress({ current: slugs.length, total: slugs.length })
      }
    } catch (err) {
      console.error('Batch character install error:', err)
      alert(`Error: ${err.message}`)
    }
    // Re-fit the CSS grid to the new roster -- this is what places the newly added
    // fighters on the character-select grid (same step the per-char path ran).
    await autoApplyCssGrid()
    setBatchAddingChars(false)
    setSelectedVaultChars(new Set())
    setShowAddCharacterModal(false)
    onRefresh()
  }

  const handleRemoveFighter = async (fighterName) => {
    if (!await appConfirm(`Remove "${fighterName}" from the project?`, {
      title: 'Remove Character',
      confirmText: 'Remove',
    })) return
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
        // Removing a fighter leaves a gap in the select-screen grid; re-fit it
        await autoApplyCssGrid()
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
