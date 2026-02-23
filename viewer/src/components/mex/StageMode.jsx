/**
 * StageMode - MEX stage variant management with Dynamic Alternate Stages (DAS)
 *
 * Features:
 * - DAS framework installation
 * - Stage list with variant counts
 * - MEX variants panel with button token assignment
 * - Available variants panel with batch selection/import
 * - Button token UI for variant assignment
 */
import { useState, useEffect, useRef } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import ConfirmDialog from '../shared/ConfirmDialog'
import { BACKEND_URL } from '../../config'

const DAS_STAGES = [
  { code: 'GrOp', name: 'Dreamland', folder: 'dreamland', vanillaImage: `${BACKEND_URL}/vanilla/stages/dreamland.png` },
  { code: 'GrPs', name: 'Pokemon Stadium', folder: 'pokemon_stadium', vanillaImage: `${BACKEND_URL}/vanilla/stages/pokemon stadium.png` },
  { code: 'GrSt', name: "Yoshi's Story", folder: 'yoshis_story', vanillaImage: `${BACKEND_URL}/vanilla/stages/yoshis story.png` },
  { code: 'GrNBa', name: 'Battlefield', folder: 'battlefield', vanillaImage: `${BACKEND_URL}/vanilla/stages/battlefield.png` },
  { code: 'GrIz', name: 'Fountain of Dreams', folder: 'fountain_of_dreams', vanillaImage: `${BACKEND_URL}/vanilla/stages/fountain of dreams.png` },
  { code: 'GrNLa', name: 'Final Destination', folder: 'final_destination', vanillaImage: `${BACKEND_URL}/vanilla/stages/final destination.png` }
]

export default function StageMode({
  mode,
  onModeChange,
  onRefresh,
  refreshing,
  API_URL
}) {
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

    for (let i = 0; i < variantsToImport.length; i++) {
      const zipPath = variantsToImport[i]
      const variant = storageVariants.find(v => v.zipPath === zipPath)

      if (!variant) {
        failCount++
        continue
      }

      setBatchProgress({ current: i + 1, total })

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
    const variantNameWithoutButton = variantNameWithoutExt.replace(/\([ABXYLRZ]\)$/i, '')
    const newVariantName = `${variantNameWithoutButton}(${buttonToAdd})`

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
    const variantNameWithoutButton = variantNameWithoutExt.replace(/\([ABXYLRZ]\)$/i, '')

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

  // Button Tokens Component
  const ButtonTokens = () => {
    const buttons = ['B', 'X', 'Y', 'L', 'R', 'Z']

    return (
      <div className="button-tokens">
        {buttons.map(btn => (
          <div
            key={btn}
            className={`button-token ${selectedButton === btn ? 'selected' : ''}`}
            onClick={() => handleButtonClick(btn)}
            title={selectedButton === btn ? `Click to deselect ${btn} button` : `Click to select ${btn} button`}
          >
            <img src={`${BACKEND_URL}/utility/buttons/${btn}.svg`} alt={btn} />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="mex-content">
      {!dasInstalled ? (
        <div className="das-install-prompt">
          <h3>Dynamic Alternate Stages Not Installed</h3>
          <p>Install the DAS framework to manage alternate stage variants for your 6 competitive stages.</p>
          <button
            className="btn-primary"
            onClick={installDAS}
            disabled={dasChecking}
          >
            {dasChecking ? 'Installing...' : 'Install DAS Framework'}
          </button>
        </div>
      ) : (
        <>
          <div className="fighters-list">
            <div className="fighters-header">
              <div className="mode-toggle">
                <button
                  className={`mode-toggle-btn ${mode === 'characters' ? 'active' : ''}`}
                  onMouseEnter={playHoverSound}
                  onClick={() => { if (mode !== 'characters') { playSound('boop'); onModeChange('characters'); } }}
                >
                  Fighters
                </button>
                <button
                  className={`mode-toggle-btn ${mode === 'stages' ? 'active' : ''}`}
                  onMouseEnter={playHoverSound}
                  onClick={() => { if (mode !== 'stages') { playSound('boop'); onModeChange('stages'); } }}
                >
                  Stages
                </button>
              </div>
              <span className="fighters-count">{DAS_STAGES.length}</span>
            </div>
            <div className="fighter-items">
              {DAS_STAGES.map(stage => {
                const availableVariants = getVariantsForStage(stage.code)
                const mexCount = mexVariantCounts[stage.code] || 0
                return (
                  <div
                    key={stage.code}
                    className={`fighter-item ${selectedStage?.code === stage.code ? 'selected' : ''}`}
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('boop'); setSelectedStage(stage); }}
                  >
                    <div className="fighter-name">{stage.name}</div>
                    <div className="fighter-info">
                      <span className="costume-count">{mexCount} in MEX</span>
                      {availableVariants.length > 0 && (
                        <span className="available-count">{availableVariants.length} available</span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className={`costumes-panel ${refreshing ? 'refreshing' : ''}`}>
            {selectedStage ? (
              <>
                <div className="costumes-section">
                  <div className="costumes-section-header">
                    <h3>In ISO ({dataReady ? mexVariants.length : 'Loading...'})</h3>
                    <ButtonTokens />
                  </div>
                  <div className="costume-list existing">
                    {mexVariants.map((variant, idx) => {
                      const isVanilla = variant.filename?.startsWith('vanilla')
                      const imageUrl = isVanilla
                        ? selectedStage.vanillaImage
                        : (variant.screenshotUrl ? `${BACKEND_URL}${variant.screenshotUrl}` : null)
                      const hasImage = isVanilla ? true : variant.hasScreenshot
                      const canAssignButton = selectedButton && variant.button !== selectedButton

                      return (
                        <div
                          key={idx}
                          className={`costume-card existing-costume ${canAssignButton ? 'button-assignable' : ''} ${dataReady ? 'card-visible' : 'card-hidden'}`}
                          onMouseEnter={playHoverSound}
                          onClick={() => handleVariantClick(variant)}
                          style={{ cursor: canAssignButton ? 'pointer' : 'default', animationDelay: dataReady ? `${idx * 30}ms` : '0ms' }}
                        >
                          <div className="costume-preview">
                            {hasImage && (
                              <img
                                src={imageUrl}
                                alt={variant.name}
                                onError={(e) => e.target.style.display = 'none'}
                              />
                            )}
                            <button
                              className="btn-remove"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleRemoveVariant(selectedStage.code, variant.name)
                              }}
                              disabled={removing}
                              title="Remove variant"
                            >
                              ×
                            </button>
                            {/* Button badge overlay */}
                            {variant.button && (
                              <div
                                className="button-badge-overlay"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleRemoveButton(variant)
                                }}
                                title={`Click to remove ${variant.button} button`}
                              >
                                <img src={`${BACKEND_URL}/utility/buttons/${variant.button}.svg`} alt={variant.button} />
                              </div>
                            )}
                          </div>
                          <div className="costume-info">
                            <h4>{variant.name}</h4>
                          </div>
                        </div>
                      )
                    })}
                    {dataReady && mexVariants.length === 0 && (
                      <div className="no-costumes">
                        <p>No variants in MEX yet</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="costumes-section">
                  <div className="costumes-section-header">
                    <h3>
                      Available to Import ({dataReady ? getVariantsForStage(selectedStage.code).length : 'Loading...'})
                      {selectedVariants.size > 0 && ` - ${selectedVariants.size} selected`}
                    </h3>
                    {getVariantsForStage(selectedStage.code).length > 0 && (
                      <div className="batch-controls">
                        {selectedVariants.size > 0 ? (
                          <>
                            <button
                              className="btn-batch-import"
                              onMouseEnter={playHoverSound}
                              onClick={() => { playSound('start'); handleBatchImportVariants(); }}
                              disabled={batchImporting}
                            >
                              {batchImporting
                                ? `Importing ${batchProgress.current}/${batchProgress.total}...`
                                : `Import Selected (${selectedVariants.size})`}
                            </button>
                            <button
                              className="btn-clear-selection"
                              onMouseEnter={playHoverSound}
                              onClick={() => { playSound('boop'); clearVariantSelection(); }}
                              disabled={batchImporting}
                            >
                              Clear
                            </button>
                          </>
                        ) : (
                          <button
                            className="btn-select-all"
                            onMouseEnter={playHoverSound}
                            onClick={() => { playSound('boop'); selectAllVariants(); }}
                          >
                            Select All
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="costume-list" ref={availableListRef}>
                    {getVariantsForStage(selectedStage.code).map((variant, idx) => {
                      const isVanilla = variant.filename?.startsWith('vanilla')
                      const imageUrl = isVanilla
                        ? selectedStage.vanillaImage
                        : (variant.screenshotUrl ? `${BACKEND_URL}${variant.screenshotUrl}` : null)
                      const hasImage = isVanilla ? true : variant.hasScreenshot
                      const isSelected = selectedVariants.has(variant.zipPath)
                      const cascadeDelay = (mexVariants.length + idx) * 30

                      return (
                        <div
                          key={idx}
                          className={`costume-card ${isSelected ? 'selected' : ''} ${dataReady ? 'card-visible' : 'card-hidden'}`}
                          style={{ animationDelay: dataReady ? `${cascadeDelay}ms` : '0ms' }}
                          onMouseEnter={playHoverSound}
                          onClick={() => { if (!batchImporting) { playSound('boop'); toggleVariantSelection(variant.zipPath); } }}
                        >
                          <div className="costume-preview">
                            {hasImage && (
                              <img
                                src={imageUrl}
                                alt={variant.name}
                                onError={(e) => e.target.style.display = 'none'}
                              />
                            )}
                            <input
                              type="checkbox"
                              className="costume-checkbox"
                              checked={isSelected}
                              onChange={() => {}}
                              disabled={batchImporting}
                            />
                            {variant.slippi_safe && (
                              <div className="slippi-badge slippi-badge-overlay" title="Slippi Safe">
                                ✓
                              </div>
                            )}
                          </div>
                          <div className="costume-info">
                            <h4>{variant.name}</h4>
                          </div>
                        </div>
                      )
                    })}
                    {dataReady && getVariantsForStage(selectedStage.code).length === 0 && (
                      <div className="no-costumes">
                        <p>No variants available in storage for {selectedStage.name}</p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="no-selection">
                <p>Select a stage to view variants</p>
              </div>
            )}
          </div>

          {/* Import Loading Overlay */}
          {(importing || batchImporting) && (
            <div className="import-overlay">
              <div className="import-modal">
                <div className="import-spinner"></div>
                <h3>Importing...</h3>
                {batchImporting && batchProgress.total > 0 && (
                  <div className="import-progress">
                    <div
                      className="import-progress-bar"
                      style={{ width: `${(batchProgress.current / batchProgress.total) * 100}%` }}
                    />
                  </div>
                )}
                <p>{batchImporting && batchProgress.total > 0
                  ? `${batchProgress.current} of ${batchProgress.total} variants`
                  : 'Please wait...'}</p>
              </div>
            </div>
          )}
        </>
      )}

      <ConfirmDialog
        show={showConfirmDialog}
        title="Remove Variant"
        message={pendingRemoval ? `Are you sure you want to remove "${pendingRemoval.variantName}"?` : ''}
        confirmText="Remove"
        onConfirm={confirmRemoveVariant}
        onCancel={() => { setShowConfirmDialog(false); setPendingRemoval(null); }}
      />
    </div>
  )
}
