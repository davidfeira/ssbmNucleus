import { useState, useEffect, useCallback } from 'react'
import { playSound } from '../../../utils/sounds'

/**
 * useExtrasManager - State + API logic for the character extras page.
 * Owns the extras list fetch, type selection, editor modal state,
 * and import/delete/save handlers.
 */
export default function useExtrasManager({ character, API_URL, onRefresh }) {
  const [selectedType, setSelectedType] = useState(null)
  const [extras, setExtras] = useState({})
  const [loading, setLoading] = useState(true)
  const [showEditor, setShowEditor] = useState(false)
  const [editingMod, setEditingMod] = useState(null)
  const [uploading, setUploading] = useState(false)

  // Fetch extras for this character
  const fetchExtras = useCallback(async () => {
    if (!character) return
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/storage/extras/list/${character}`)
      const data = await response.json()
      if (data.success) {
        setExtras(data.extras || {})
      } else {
        setExtras({})
      }
    } catch (err) {
      console.error('[ExtrasPageView] Fetch error:', err)
      setExtras({})
    } finally {
      setLoading(false)
    }
  }, [character, API_URL])

  useEffect(() => {
    fetchExtras()
  }, [fetchExtras])

  const handleRefresh = () => {
    fetchExtras()
    onRefresh?.()
  }

  const handleCreateNew = () => {
    setEditingMod(null)
    setShowEditor(true)
  }

  const handleEdit = (mod) => {
    setEditingMod(mod)
    setShowEditor(true)
  }

  const handleDelete = () => {
    handleRefresh()
  }

  const handleImport = async () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.dat'
    input.onchange = async (e) => {
      const file = e.target.files?.[0]
      if (!file) return

      setUploading(true)
      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('character', character)
        formData.append('extraType', selectedType.id)

        const response = await fetch(`${API_URL}/storage/extras/import`, {
          method: 'POST',
          body: formData
        })

        const data = await response.json()
        if (data.success) {
          handleRefresh()
        } else {
          alert(`Import failed: ${data.error}`)
        }
      } catch (err) {
        console.error('[ExtrasPageView] Import error:', err)
        alert(`Import error: ${err.message}`)
      } finally {
        setUploading(false)
      }
    }
    input.click()
  }

  const handleEditorClose = () => {
    playSound('back')
    setShowEditor(false)
    setEditingMod(null)
  }

  const handleSave = () => {
    handleRefresh()
  }

  return {
    selectedType,
    setSelectedType,
    extras,
    loading,
    uploading,
    showEditor,
    editingMod,
    handleCreateNew,
    handleEdit,
    handleDelete,
    handleImport,
    handleEditorClose,
    handleSave
  }
}
