/**
 * useStageVariants - DAS (Dynamic Alternate Stages) state and logic for StageMode
 *
 * Covers: DAS install check/install, storage + MEX variant fetching,
 * single/batch import, removal (with confirm dialog), button token
 * assignment/removal via rename, and available-variant selection.
 */
import { useState, useEffect, useRef } from 'react'
import { playSound } from '../../../utils/sounds'
import { BACKEND_URL } from '../../../config'

export const DAS_STAGES = [
  { code: 'GrOp', name: 'Dreamland', folder: 'dreamland', vanillaImage: `${BACKEND_URL}/vanilla/stages/dreamland.png` },
  { code: 'GrPs', name: 'Pokemon Stadium', folder: 'pokemon_stadium', vanillaImage: `${BACKEND_URL}/vanilla/stages/pokemon stadium.png` },
  { code: 'GrSt', name: "Yoshi's Story", folder: 'yoshis_story', vanillaImage: `${BACKEND_URL}/vanilla/stages/yoshis story.png` },
  { code: 'GrNBa', name: 'Battlefield', folder: 'battlefield', vanillaImage: `${BACKEND_URL}/vanilla/stages/battlefield.png` },
  { code: 'GrIz', name: 'Fountain of Dreams', folder: 'fountain_of_dreams', vanillaImage: `${BACKEND_URL}/vanilla/stages/fountain of dreams.png` },
  { code: 'GrNLa', name: 'Final Destination', folder: 'final_destination', vanillaImage: `${BACKEND_URL}/vanilla/stages/final destination.png` }
]

const BUTTON_TOKEN_REGEX = /\s*\(([ABXYLRZ])\)$/i

function normalizeWhitespace(name) {
  return name.replace(/\s+/g, ' ').trim()
}

function toProjectVariantBaseName(name) {
  const words = normalizeWhitespace(name)
    .match(/[A-Za-z0-9]+/g)

  if (!words || words.length === 0) {
    return normalizeWhitespace(name).replace(/\s+/g, '')
  }

  return words.map(word => word.charAt(0).toUpperCase() + word.slice(1)).join('')
}

function stripButtonIndicator(name) {
  return normalizeWhitespace(name.replace(BUTTON_TOKEN_REGEX, ''))
}

function addButtonIndicator(name, button) {
  return `${toProjectVariantBaseName(stripButtonIndicator(name))}(${button})`
}

function normalizeProjectVariantName(name) {
  const normalized = normalizeWhitespace(name)
  const match = normalized.match(BUTTON_TOKEN_REGEX)
  const baseName = toProjectVariantBaseName(stripButtonIndicator(normalized))

  if (match) {
    return `${baseName}(${match[1].toUpperCase()})`
  }

  return baseName
}

export default function useStageVariants({ API_URL, onRefresh }) {
  const [dasInstalled, setDasInstalled] = useState(false)
  const [dasChecking, setDasChecking] = useState(false)
  const [selectedStage, setSelectedStage] = useState(null)
  const [storageVariants, setStorageVariants] = useState([])
  const [mexVariants, setMexVariants] = useState([])
  const [mexVariantCounts, setMexVariantCounts] = useState({})
  const [selectedVariants, setSelectedVariants] = useState(new Set())
  const [selectedButton, setSelectedButton] = useState(null)
  const [importing, setImporting] = useState(false)
  const [importingCostume, setImportingCostume] = useState(null)
  const [removing, setRemoving] = useState(false)
  const [batchImporting, setBatchImporting] = useState(false)
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 })
  const [dataReady, setDataReady] = useState(false)

  // Confirm dialog state for removing variants
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [pendingRemoval, setPendingRemoval] = useState(null)

  // Ref for scrolling Available to Import list to top on stage change
  const availableListRef = useRef(null)

  useEffect(() => {
    checkDASInstallation()
    fetchStorageVariants()
    fetchAllMexVariantCounts()
  }, [])

  useEffect(() => {
    if (selectedStage?.isCustom) {
      setDataReady(true)
      return
    }
    if (selectedStage && dasInstalled) {
      setDataReady(false)
      setMexVariants([])
      setSelectedVariants(new Set())
      setSelectedButton(null)
      fetchMexVariants(selectedStage.code)
      // Reset scroll position of Available to Import list
      if (availableListRef.current) {
        availableListRef.current.scrollTop = 0
      }
    }
  }, [selectedStage, dasInstalled])

  const checkDASInstallation = async () => {
    setDasChecking(true)
    try {
      const response = await fetch(`${API_URL}/das/status`)
      const data = await response.json()
      if (data.success) {
        setDasInstalled(data.installed)
      }
    } catch (err) {
      console.error('Failed to check DAS status:', err)
    } finally {
      setDasChecking(false)
    }
  }

  const installDAS = async () => {
    if (!confirm('Install Dynamic Alternate Stages framework? This will modify stage files in your MEX project.')) {
      return
    }

    setDasChecking(true)
    try {
      const response = await fetch(`${API_URL}/das/install`, {
        method: 'POST'
      })
      const data = await response.json()

      if (data.success) {
        alert('DAS framework installed successfully!')
        setDasInstalled(true)
        fetchStorageVariants()
      } else {
        alert(`DAS installation failed: ${data.error}`)
      }
    } catch (err) {
      console.error('DAS installation error:', err)
      alert(`DAS installation error: ${err.message}`)
    } finally {
      setDasChecking(false)
    }
  }

  const fetchStorageVariants = async () => {
    try {
      const response = await fetch(`${API_URL}/das/storage/variants`)
      const data = await response.json()
      if (data.success) {
        setStorageVariants(data.variants)
      }
    } catch (err) {
      console.error('Failed to fetch storage variants:', err)
    }
  }

  const fetchMexVariants = async (stageCode) => {
    try {
      const response = await fetch(`${API_URL}/das/stages/${stageCode}/variants`)
      const data = await response.json()
      if (data.success) {
        setMexVariants(data.variants || [])
      }
    } catch (err) {
      console.error('Failed to fetch MEX variants:', err)
      setMexVariants([])
    } finally {
      setTimeout(() => setDataReady(true), 50)
    }
  }

  const fetchAllMexVariantCounts = async () => {
    try {
      const counts = {}
      await Promise.all(
        DAS_STAGES.map(async (stage) => {
          const response = await fetch(`${API_URL}/das/stages/${stage.code}/variants`)
          const data = await response.json()
          if (data.success) {
            counts[stage.code] = data.variants?.length || 0
          }
        })
      )
      setMexVariantCounts(counts)
    } catch (err) {
      console.error('Failed to fetch MEX variant counts:', err)
    }
  }

  const handleImportVariant = async (variant) => {
    if (importing) return

    setImporting(true)
    setImportingCostume(variant.zipPath)

    try {
      const response = await fetch(`${API_URL}/das/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stageCode: variant.stageCode,
          variantPath: variant.zipPath
        })
      })

      const data = await response.json()

      if (data.success) {
        console.log(`✓ Successfully imported variant to ${variant.stageName}`)
        await onRefresh()
        await fetchMexVariants(selectedStage.code)
        await fetchStorageVariants()
        await fetchAllMexVariantCounts()
      } else {
        alert(`Import failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Import error:', err)
      alert(`Import error: ${err.message}`)
    } finally {
      setImporting(false)
      setImportingCostume(null)
    }
  }

  const handleBatchImportVariants = async () => {
    if (selectedVariants.size === 0 || batchImporting) return

    setBatchImporting(true)
    const variantsToImport = Array.from(selectedVariants)
    const total = variantsToImport.length
    setBatchProgress({ current: 0, total })

    let successCount = 0
    let failCount = 0
    let completedCount = 0
    const markBatchStepComplete = () => {
      completedCount += 1
      setBatchProgress({ current: completedCount, total })
    }

    for (let i = 0; i < variantsToImport.length; i++) {
      const zipPath = variantsToImport[i]
      const variant = storageVariants.find(v => v.zipPath === zipPath)

      if (!variant) {
        failCount++
        markBatchStepComplete()
        continue
      }

      try {
        const response = await fetch(`${API_URL}/das/import`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stageCode: variant.stageCode,
            variantPath: variant.zipPath
          })
        })

        const data = await response.json()

        if (data.success) {
          successCount++
        } else {
          console.error(`Import failed for ${variant.name}:`, data.error)
          failCount++
        }
      } catch (err) {
        console.error(`Import error for ${variant.name}:`, err)
        failCount++
      } finally {
        markBatchStepComplete()
      }
    }

    // Refresh once at the end
    await onRefresh()
    if (selectedStage) {
      await fetchMexVariants(selectedStage.code)
    }
    await fetchStorageVariants()
    await fetchAllMexVariantCounts()

    // Clear selections
    setSelectedVariants(new Set())
    setBatchImporting(false)
    setBatchProgress({ current: 0, total: 0 })

    // Show summary
    if (failCount > 0) {
      playSound('error')
      alert(`Batch import completed:\n${successCount} succeeded, ${failCount} failed`)
    } else {
      playSound('newSkin')
      console.log(`✓ Successfully imported ${successCount} stage variant(s)`)
    }
  }

  const handleButtonClick = (button) => {
    setSelectedButton(selectedButton === button ? null : button)
  }

  const handleVariantClick = async (variant) => {
    if (!selectedButton) return

    if (variant.button === selectedButton) {
      console.log(`Variant already has button ${selectedButton}`)
      return
    }

    const buttonToAdd = selectedButton
    const variantNameWithoutExt = variant.name
    const newVariantName = addButtonIndicator(variantNameWithoutExt, buttonToAdd)

    try {
      const response = await fetch(`${API_URL}/das/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stageCode: variant.stageCode,
          oldName: variantNameWithoutExt,
          newName: newVariantName
        })
      })

      const data = await response.json()

      if (data.success) {
        console.log(`✓ Added button ${buttonToAdd} to ${variant.name}`)
        setSelectedButton(null)
        await fetchMexVariants(selectedStage.code)
      } else {
        alert(`Failed to add button: ${data.error}`)
      }
    } catch (err) {
      console.error('Button add error:', err)
      alert(`Error adding button: ${err.message}`)
    }
  }

  const handleRemoveButton = async (variant) => {
    if (!variant.button) return

    const variantNameWithoutExt = variant.name
    const variantNameWithoutButton = normalizeProjectVariantName(stripButtonIndicator(variantNameWithoutExt))

    try {
      const response = await fetch(`${API_URL}/das/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stageCode: variant.stageCode,
          oldName: variantNameWithoutExt,
          newName: variantNameWithoutButton
        })
      })

      const data = await response.json()

      if (data.success) {
        console.log(`✓ Removed button ${variant.button} from ${variant.name}`)
        await fetchMexVariants(selectedStage.code)
      } else {
        alert(`Failed to remove button: ${data.error}`)
      }
    } catch (err) {
      console.error('Button remove error:', err)
      alert(`Error removing button: ${err.message}`)
    }
  }

  const handleRemoveVariant = (stageCode, variantName) => {
    if (removing) return

    // Show confirm dialog instead of native confirm()
    setPendingRemoval({ stageCode, variantName })
    setShowConfirmDialog(true)
  }

  const confirmRemoveVariant = async () => {
    if (!pendingRemoval) return

    const { stageCode, variantName } = pendingRemoval
    setShowConfirmDialog(false)
    setPendingRemoval(null)
    setRemoving(true)

    try {
      const response = await fetch(`${API_URL}/das/remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stageCode: stageCode,
          variantName: variantName
        })
      })

      const data = await response.json()

      if (data.success) {
        console.log(`✓ Successfully removed "${variantName}"`)
        await onRefresh()
        await fetchMexVariants(selectedStage.code)
        await fetchStorageVariants()
        await fetchAllMexVariantCounts()
      } else {
        alert(`Remove failed: ${data.error}`)
      }
    } catch (err) {
      console.error('Remove error:', err)
      alert(`Remove error: ${err.message}`)
    } finally {
      setRemoving(false)
    }
  }

  const getVariantsForStage = (stageCode) => {
    return storageVariants.filter(v => v.stageCode === stageCode)
  }

  const toggleVariantSelection = (zipPath) => {
    setSelectedVariants(prev => {
      const newSet = new Set(prev)
      if (newSet.has(zipPath)) {
        newSet.delete(zipPath)
      } else {
        newSet.add(zipPath)
      }
      return newSet
    })
  }

  const selectAllVariants = () => {
    if (!selectedStage) return
    const allVariants = getVariantsForStage(selectedStage.code)
    setSelectedVariants(new Set(allVariants.map(v => v.zipPath)))
  }

  const clearVariantSelection = () => {
    setSelectedVariants(new Set())
  }

  return {
    dasInstalled,
    dasChecking,
    selectedStage,
    setSelectedStage,
    storageVariants,
    mexVariants,
    mexVariantCounts,
    selectedVariants,
    selectedButton,
    importing,
    importingCostume,
    removing,
    batchImporting,
    batchProgress,
    dataReady,
    showConfirmDialog,
    setShowConfirmDialog,
    pendingRemoval,
    setPendingRemoval,
    availableListRef,
    installDAS,
    handleImportVariant,
    handleBatchImportVariants,
    handleButtonClick,
    handleVariantClick,
    handleRemoveButton,
    handleRemoveVariant,
    confirmRemoveVariant,
    getVariantsForStage,
    toggleVariantSelection,
    selectAllVariants,
    clearVariantSelection
  }
}
