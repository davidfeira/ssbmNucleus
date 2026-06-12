/**
 * ProjectHeaderInfo - left side of the install-page header. Shows the disc banner
 * thumbnail plus the long name / long maker as inline-editable fields. Clicking the
 * banner (pencil on hover) opens the full BuildInfoModal (short name/maker, image, …).
 *
 * The long name defaults to the project (folder) name when unset; committing a field
 * (blur / Enter) persists it via onSaveField.
 */
import React, { useEffect, useRef, useState } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import { rgbaToDataUrl } from '../../utils/banner'

export default function ProjectHeaderInfo({ buildInfo, projectName, onOpenBanner, onSaveField }) {
  const storedLongName = buildInfo?.longName || ''
  const storedLongMaker = buildInfo?.longMaker || ''

  const [longName, setLongName] = useState(storedLongName || projectName || '')
  const [longMaker, setLongMaker] = useState(storedLongMaker)
  const [savingField, setSavingField] = useState(null)
  const nameInputRef = useRef(null)
  const makerInputRef = useRef(null)
  // Set when Escape cancels an edit so the resulting blur reverts instead of committing.
  const escapedRef = useRef(false)

  // Re-sync drafts whenever the underlying build info (or project) changes —
  // but never overwrite a field the user is currently typing in (a refetch
  // landing mid-edit used to reset the input under the cursor).
  useEffect(() => {
    if (document.activeElement !== nameInputRef.current) {
      setLongName(storedLongName || projectName || '')
    }
    if (document.activeElement !== makerInputRef.current) {
      setLongMaker(storedLongMaker)
    }
  }, [storedLongName, storedLongMaker, projectName])

  const bannerSrc = buildInfo
    ? rgbaToDataUrl(buildInfo.bannerRgbaBase64, buildInfo.bannerWidth, buildInfo.bannerHeight)
    : null

  const commit = async (field, value, stored, fallback) => {
    if (value === stored) return
    setSavingField(field)
    try {
      await onSaveField({ [field]: value })
    } catch (e) {
      // revert the draft on failure
      if (field === 'longName') setLongName(stored || fallback || '')
      else setLongMaker(stored)
    } finally {
      setSavingField(null)
    }
  }

  return (
    <div className="mex-build-header">
      <span className="status-dot" />

      <button
        type="button"
        className="mex-banner-thumb"
        title="Edit banner & info"
        onMouseEnter={playHoverSound}
        onClick={() => { playSound('start'); onOpenBanner() }}
      >
        {bannerSrc ? (
          <img src={bannerSrc} alt="Banner" />
        ) : (
          <span className="mex-banner-thumb__empty">banner</span>
        )}
        <span className="mex-banner-thumb__pencil">✎</span>
      </button>

      <div className="mex-build-fields">
        <input
          ref={nameInputRef}
          className="mex-inline-input mex-inline-input--name"
          value={longName}
          placeholder={projectName || 'Game name'}
          maxLength={63}
          spellCheck={false}
          onChange={(e) => setLongName(e.target.value)}
          onBlur={() => {
            if (escapedRef.current) { escapedRef.current = false; return }
            commit('longName', longName, storedLongName, projectName)
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') e.currentTarget.blur()
            if (e.key === 'Escape') {
              escapedRef.current = true
              setLongName(storedLongName || projectName || '')
              e.currentTarget.blur()
            }
          }}
        />
        <input
          ref={makerInputRef}
          className="mex-inline-input mex-inline-input--maker"
          value={longMaker}
          placeholder="Creator"
          maxLength={63}
          spellCheck={false}
          onChange={(e) => setLongMaker(e.target.value)}
          onBlur={() => {
            if (escapedRef.current) { escapedRef.current = false; return }
            commit('longMaker', longMaker, storedLongMaker)
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') e.currentTarget.blur()
            if (e.key === 'Escape') {
              escapedRef.current = true
              setLongMaker(storedLongMaker)
              e.currentTarget.blur()
            }
          }}
        />
      </div>

      {savingField && <span className="mex-build-saving">saving…</span>}
    </div>
  )
}
