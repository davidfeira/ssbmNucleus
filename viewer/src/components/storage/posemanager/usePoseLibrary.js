import { useState, useEffect, useCallback } from 'react'
import { playSound } from '../../../utils/sounds'

/**
 * Pose list management + save/delete API calls for the Pose Manager.
 */
export default function usePoseLibrary({ show, character, API_URL, viewerRef }) {
  const [poseName, setPoseName] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [poses, setPoses] = useState([])
  const [loadingPoses, setLoadingPoses] = useState(true)
  const [selectedPose, setSelectedPose] = useState(null) // For skin selector modal

  // Fetch saved poses
  const fetchPoses = useCallback(async () => {
    if (!character) return
    try {
      const response = await fetch(`${API_URL}/storage/poses/list/${character}`)
      const data = await response.json()
      if (data.success) {
        setPoses(data.poses)
      }
    } catch (err) {
      console.error('[PoseManager] Fetch poses error:', err)
    } finally {
      setLoadingPoses(false)
    }
  }, [character, API_URL])

  useEffect(() => {
    if (show) {
      fetchPoses()
    }
  }, [show, fetchPoses])

  const handleSavePose = async () => {
    if (!poseName.trim()) {
      setSaveError('Please enter a pose name')
      return
    }

    if (!viewerRef.current) {
      setSaveError('Viewer not ready')
      return
    }

    setSaving(true)
    setSaveError(null)
    setSaveSuccess(false)

    try {
      // Export scene from viewer
      const sceneData = await viewerRef.current.exportScene()
      if (!sceneData) {
        throw new Error('Failed to export scene data')
      }
      // No client-side animation guard: a pose is valid either with a picked
      // AJ animation OR with a scene-mode character's baked pose (no symbol).
      // The backend decides and returns a clear error for the bind-pose case.

      // Save pose via API
      const response = await fetch(`${API_URL}/storage/poses/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character,
          poseName: poseName.trim(),
          sceneData
        })
      })

      const data = await response.json()
      if (!data.success) {
        throw new Error(data.error || 'Failed to save pose')
      }

      playSound('camera')
      setSaveSuccess(true)
      setPoseName('')

      // Refresh poses list to show new thumbnail
      await fetchPoses()

      // Clear success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err) {
      console.error('[PoseManager] Save error:', err)
      setSaveError(err.message || 'Failed to save pose')
    } finally {
      setSaving(false)
    }
  }

  const handleDeletePose = (poseName) => {
    setPoses(poses.filter(p => p.name !== poseName))
  }

  return {
    poseName,
    setPoseName,
    saving,
    saveError,
    saveSuccess,
    poses,
    loadingPoses,
    selectedPose,
    setSelectedPose,
    handleSavePose,
    handleDeletePose
  }
}
