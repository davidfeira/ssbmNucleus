/**
 * VariantsPanel - DAS variant view of StageMode for the selected stage:
 * variants in the ISO (with button token assignment/removal) and storage
 * variants available to import (with batch controls).
 */
import { useState } from 'react'
import { playSound, playHoverSound } from '../../../utils/sounds'
import { BACKEND_URL, API_URL } from '../../../config'
import PaginationBar from '../../shared/PaginationBar'
import usePagination from '../../shared/usePagination'
import SongPacksModal from '../../storage/SongPacksModal'

const MusicIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 18V5l12-2v13" />
    <circle cx="6" cy="18" r="3" />
    <circle cx="18" cy="16" r="3" />
  </svg>
)

export default function VariantsPanel({ sm }) {
  const { selectedStage, mexVariants, dataReady } = sm
  const availableVariants = sm.getVariantsForStage(selectedStage.code)
  const inIsoPager = usePagination(mexVariants.length, `${selectedStage.code}-iso`)
  const availPager = usePagination(availableVariants.length, `${selectedStage.code}-avail`)

  // Song pack browser (stage music playlists, stored in the vault and
  // installed into the project explicitly)
  const [showSongPacks, setShowSongPacks] = useState(false)

  // Button Tokens Component
  const ButtonTokens = () => {
    const buttons = ['B', 'X', 'Y', 'L', 'R', 'Z']

    return (
      <div className="button-tokens">
        {buttons.map(btn => (
          <div
            key={btn}
            className={`button-token ${sm.selectedButton === btn ? 'selected' : ''}`}
            onClick={() => sm.handleButtonClick(btn)}
            title={sm.selectedButton === btn ? `Click to deselect ${btn} button` : `Click to select ${btn} button`}
          >
            <img src={`${BACKEND_URL}/utility/buttons/${btn}.svg`} alt={btn} />
          </div>
        ))}
      </div>
    )
  }

  return (
    <>
      <div className="costumes-section">
        <div className="costumes-section-header">
          <h3>In ISO ({dataReady ? mexVariants.length : 'Loading...'})</h3>
          <div className="iso-mod-actions">
            <button
              className="btn-pose-all btn-sound-pack"
              onClick={() => { playSound('boop'); setShowSongPacks(true); }}
              onMouseEnter={playHoverSound}
              title="Song packs — choose which music this stage plays in this project"
            >
              <MusicIcon />
            </button>
          </div>
          <ButtonTokens />
        </div>
        <div className="costume-list existing">
          {mexVariants.slice(inIsoPager.start, inIsoPager.end).map((variant, i) => {
            const idx = inIsoPager.start + i
            const isVanilla = variant.filename?.startsWith('vanilla')
            const imageUrl = isVanilla
              ? selectedStage.vanillaImage
              : (variant.screenshotUrl ? `${BACKEND_URL}${variant.screenshotUrl}` : null)
            const hasImage = isVanilla ? true : variant.hasScreenshot
            const canAssignButton = sm.selectedButton && variant.button !== sm.selectedButton

            return (
              <div
                key={idx}
                className={`costume-card existing-costume ${canAssignButton ? 'button-assignable' : ''} ${dataReady ? 'card-visible' : 'card-hidden'}`}
                onMouseEnter={playHoverSound}
                onClick={() => sm.handleVariantClick(variant)}
                style={{ cursor: canAssignButton ? 'pointer' : 'default', animationDelay: dataReady ? `${Math.min(i * 30, 990)}ms` : '0ms' }}
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
                      sm.handleRemoveVariant(selectedStage.code, variant.name)
                    }}
                    disabled={sm.removing}
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
                        sm.handleRemoveButton(variant)
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
        <PaginationBar pager={inIsoPager} />
      </div>

      <div className="costumes-section">
        <div className="costumes-section-header">
          <h3>
            Available to Import ({dataReady ? availableVariants.length : 'Loading...'})
            {sm.selectedVariants.size > 0 && ` - ${sm.selectedVariants.size} selected`}
          </h3>
          {availableVariants.length > 0 && (
            <div className="batch-controls">
              {sm.selectedVariants.size > 0 ? (
                <>
                  <button
                    className="btn-batch-import"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('start'); sm.handleBatchImportVariants(); }}
                    disabled={sm.batchImporting}
                  >
                    {sm.batchImporting
                      ? `Importing ${sm.batchProgress.current}/${sm.batchProgress.total}...`
                      : `Import Selected (${sm.selectedVariants.size})`}
                  </button>
                  <button
                    className="btn-clear-selection"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('boop'); sm.clearVariantSelection(); }}
                    disabled={sm.batchImporting}
                  >
                    Clear
                  </button>
                </>
              ) : (
                <button
                  className="btn-select-all"
                  onMouseEnter={playHoverSound}
                  onClick={() => { playSound('boop'); sm.selectAllVariants(); }}
                >
                  Select All
                </button>
              )}
            </div>
          )}
        </div>
        <div className="costume-list" ref={sm.availableListRef}>
          {availableVariants.slice(availPager.start, availPager.end).map((variant, i) => {
            const idx = availPager.start + i
            const isVanilla = variant.filename?.startsWith('vanilla')
            const imageUrl = isVanilla
              ? selectedStage.vanillaImage
              : (variant.screenshotUrl ? `${BACKEND_URL}${variant.screenshotUrl}` : null)
            const hasImage = isVanilla ? true : variant.hasScreenshot
            const isSelected = sm.selectedVariants.has(variant.zipPath)

            return (
              <div
                key={idx}
                className={`costume-card ${isSelected ? 'selected' : ''} ${dataReady ? 'card-visible' : 'card-hidden'}`}
                style={{ animationDelay: dataReady ? `${Math.min(i * 30, 990)}ms` : '0ms' }}
                onMouseEnter={playHoverSound}
                onClick={() => { if (!sm.batchImporting) { playSound('boop'); sm.toggleVariantSelection(variant.zipPath); } }}
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
                    disabled={sm.batchImporting}
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
          {dataReady && availableVariants.length === 0 && (
            <div className="no-costumes">
              <p>No variants available in storage for {selectedStage.name}</p>
            </div>
          )}
        </div>
        <PaginationBar pager={availPager} />
      </div>

      <SongPacksModal
        show={showSongPacks}
        stage={selectedStage.code}
        displayName={selectedStage.name}
        installMode
        API_URL={API_URL}
        onClose={() => setShowSongPacks(false)}
      />
    </>
  )
}
