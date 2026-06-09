/**
 * useExtras - state and API logic for CharacterMode extras mode
 * (laser colors, sword trails, model swaps, etc.)
 */
import { useState, useEffect } from 'react'

export default function useExtras({ API_URL, selectedFighter }) {
  const [extrasMode, setExtrasMode] = useState(false)
  const [selectedExtraType, setSelectedExtraType] = useState(null)
  const [extraMods, setExtraMods] = useState({})
  const [selectedExtraMod, setSelectedExtraMod] = useState(null)
  const [importingExtra, setImportingExtra] = useState(false)
  const [currentColors, setCurrentColors] = useState(null)
  const [isVanilla, setIsVanilla] = useState(true)

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

  return {
    extrasMode,
    setExtrasMode,
    selectedExtraType,
    setSelectedExtraType,
    extraMods,
    selectedExtraMod,
    setSelectedExtraMod,
    importingExtra,
    currentColors,
    setCurrentColors,
    isVanilla,
    getAllMods,
    handleImportExtra,
    handleRestoreVanilla
  }
}
