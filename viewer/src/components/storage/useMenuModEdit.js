/**
 * useMenuModEdit - shared modal state for the menu-mod edit modals.
 *
 * Centralizes the open/close + name + saving/deleting flags every menu-mod
 * view needs for its MenuModEditModal, plus an editable-image picker (mirrors
 * the costume/stage screenshot replace) and a cache-bust stamp so a freshly
 * uploaded preview reloads. Each view only supplies the actual save/delete/
 * upload/export network calls.
 */
import { useState } from 'react'

export default function useMenuModEdit() {
  const [editing, setEditing] = useState(null)   // the mod being edited (or null)
  const [editName, setEditName] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [exporting, setExporting] = useState(false)

  // Pending replacement image (like the EditModal screenshot/CSP flow)
  const [newImage, setNewImage] = useState(null)        // File
  const [imagePreview, setImagePreview] = useState(null) // data URL for preview
  const [cacheBust, setCacheBust] = useState(0)          // bump to reload same-URL images

  const resetImage = () => { setNewImage(null); setImagePreview(null) }

  const open = (mod) => {
    setEditing(mod)
    setEditName(mod?.name || '')
    setSaving(false)
    setDeleting(false)
    setExporting(false)
    resetImage()
  }

  const close = () => {
    setEditing(null)
    setSaving(false)
    setDeleting(false)
    setExporting(false)
    resetImage()
  }

  const bumpCache = () => setCacheBust(Date.now())

  const handleImageChange = (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''  // allow re-picking the same file
    if (!file) return
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }
    setNewImage(file)
    const reader = new FileReader()
    reader.onload = (ev) => setImagePreview(ev.target.result)
    reader.readAsDataURL(file)
  }

  return {
    editing, setEditing,
    editName, setEditName,
    saving, setSaving,
    deleting, setDeleting,
    exporting, setExporting,
    newImage, imagePreview, handleImageChange, resetImage,
    cacheBust, bumpCache,
    open, close,
  }
}
