/**
 * IsoScanModal - Rip new content out of one or more vanilla / modded ISOs.
 *
 * Three scan targets, chosen by checkbox:
 *   - Character skins: wit-based extraction + hash filtering, live SocketIO
 *     progress, per-character CSP grid with checkboxes
 *   - Custom characters / Custom stages: m-ex extraction via a temp MexCLI
 *     project per ISO (synchronous, a minute or two per ISO); imported
 *     straight into the vault with a summary shown afterwards
 *
 * Flow:
 *   idle        → pick ISO files + scan targets, then "Start scan"
 *   scanning    → custom extraction passes first, then the skins job
 *   results     → skins CSP grid (+ custom extraction summary) → import
 *   custom-done → summary when only custom targets were scanned
 *   importing   → loader while importing selected DATs
 *   done        → success summary, refresh storage on close
 *   error       → error display, allow retry
 */

import { useEffect, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { API_URL, BACKEND_URL } from '../../config'
import { playSound, playHoverSound } from '../../utils/sounds'
import HexagonLoader from '../shared/HexagonLoader'
import './IsoScanModal.css'

const PHASE_LABEL = {
  pending: 'Preparing…',
  custom: 'Extracting m-ex content',
  extracting: 'Extracting ISOs',
  scanning: 'Hash filtering',
  slippi: 'Slippi safety check',
  csp: 'Generating thumbnails',
  complete: 'Done',
  cancelled: 'Cancelled',
  error: 'Error',
}

const TARGET_DEFAULTS = { skins: true, customCharacters: false, customStages: false }

export default function IsoScanModal({
  onClose,
  onRefresh,
  initialIsoPaths,
  initialTargets,
  onCustomCharactersChanged,
  onCustomStagesChanged
}) {
  const [phase, setPhase] = useState('idle') // idle | scanning | results | custom-done | importing | done | error
  // Seeded when the unified Import button / drag-and-drop receives .iso files
  const [isoPaths, setIsoPaths] = useState(() => initialIsoPaths || [])
  // Which scan targets to run; remembered across sessions. An explicit
  // initialTargets (e.g. the custom grids' Scan ISO buttons) wins.
  const [targets, setTargets] = useState(() => {
    if (initialTargets) return { ...TARGET_DEFAULTS, skins: false, ...initialTargets }
    try {
      return { ...TARGET_DEFAULTS, ...JSON.parse(localStorage.getItem('iso_scan_targets') || '{}') }
    } catch {
      return TARGET_DEFAULTS
    }
  })
  const [customSummary, setCustomSummary] = useState(null)
  const [witAvailable, setWitAvailable] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [progress, setProgress] = useState({ status: 'pending', percent: 0, message: '' })
  const [stats, setStats] = useState(null)
  const [characters, setCharacters] = useState({})
  const [selected, setSelected] = useState(new Set())
  const [expanded, setExpanded] = useState(new Set())
  const [importResult, setImportResult] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)

  const socketRef = useRef(null)

  // SocketIO subscription for live progress
  useEffect(() => {
    const socket = io(BACKEND_URL)
    socketRef.current = socket

    socket.on('iso_scan_progress', (data) => {
      if (jobId && data.job_id !== jobId) return
      setProgress({
        status: data.status,
        percent: data.percent || 0,
        message: data.message || '',
      })
      if (data.stats) setStats(data.stats)
    })

    socket.on('iso_scan_complete', (data) => {
      if (jobId && data.job_id !== jobId) return
      if (data.status === 'cancelled') {
        setPhase('idle')
        return
      }
      // Fetch the final state to get the grouped candidates
      fetch(`${API_URL}/iso-scan/${data.job_id}`)
        .then(r => r.json())
        .then(j => {
          if (j.success) {
            setCharacters(j.characters || {})
            setStats(j.stats || null)
            // Default: select all new skins
            const all = new Set()
            const initialExpand = new Set()
            for (const [char, skins] of Object.entries(j.characters || {})) {
              initialExpand.add(char)
              for (const s of skins) all.add(s.key)
            }
            setSelected(all)
            setExpanded(initialExpand)
            setPhase('results')
            playSound('newSkin')
          }
        })
        .catch(() => {})
    })

    socket.on('iso_scan_error', (data) => {
      if (jobId && data.job_id !== jobId) return
      setErrorMsg(data.error || 'Scan failed')
      setPhase('error')
      playSound('error')
    })

    return () => {
      try { socket.disconnect() } catch (_) {}
    }
  }, [jobId])

  // Preflight: check that wit.exe is reachable
  useEffect(() => {
    fetch(`${API_URL}/iso-scan/preflight`)
      .then(r => r.json())
      .then(d => setWitAvailable(!!d.wit_available))
      .catch(() => setWitAvailable(false))
  }, [])

  const pickFiles = async () => {
    if (!window.electron?.openIsoMultiDialog) return
    playSound('boop')
    const paths = await window.electron.openIsoMultiDialog()
    if (Array.isArray(paths) && paths.length) {
      setIsoPaths(Array.from(new Set([...isoPaths, ...paths])))
    }
  }

  const removeIso = (path) => {
    setIsoPaths(isoPaths.filter(p => p !== path))
  }

  const anyTarget = targets.skins || targets.customCharacters || targets.customStages

  const toggleTarget = (key) => {
    const next = { ...targets, [key]: !targets[key] }
    setTargets(next)
    try { localStorage.setItem('iso_scan_targets', JSON.stringify(next)) } catch { /* ignore */ }
  }

  const startScan = async () => {
    if (!isoPaths.length || !anyTarget) return
    if (targets.skins && !witAvailable) return
    playSound('start')
    setPhase('scanning')
    setProgress({ status: 'pending', percent: 0, message: 'Starting…' })
    setErrorMsg(null)
    setCustomSummary(null)

    // Custom m-ex extraction passes run first. Each builds a temp MexCLI
    // project per ISO, so these are synchronous and take a minute or two
    // per ISO per target.
    const customTargets = [
      targets.customCharacters && ['characters', 'custom-characters', 'custom characters'],
      targets.customStages && ['stages', 'custom-stages', 'custom stages'],
    ].filter(Boolean)

    if (customTargets.length) {
      const summary = {}
      const totalSteps = customTargets.length * isoPaths.length
      let step = 0
      for (const [key, route, label] of customTargets) {
        const acc = { imported: [], skipped: [], errors: [] }
        for (const isoPath of isoPaths) {
          const isoName = isoPath.split(/[\\/]/).pop()
          setProgress({
            status: 'custom',
            percent: Math.round((step / totalSteps) * 100),
            message: `Extracting ${label} from ${isoName}…`,
          })
          try {
            const res = await fetch(`${API_URL}/${route}/scan-iso`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ isoPath }),
            })
            const data = await res.json()
            if (data.success) {
              acc.imported.push(...(data.imported || []))
              acc.skipped.push(...(data.skipped || []))
            } else {
              acc.errors.push(`${isoName}: ${data.error || 'failed'}`)
            }
          } catch (e) {
            acc.errors.push(`${isoName}: ${e.message}`)
          }
          step += 1
        }
        summary[key] = acc
      }
      setCustomSummary(summary)
      if (summary.characters?.imported.length) onCustomCharactersChanged?.()
      if (summary.stages?.imported.length) onCustomStagesChanged?.()
    }

    if (!targets.skins) {
      setPhase('custom-done')
      playSound('newSkin')
      return
    }

    try {
      const res = await fetch(`${API_URL}/iso-scan/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ iso_paths: isoPaths }),
      })
      const data = await res.json()
      if (!data.success) {
        setErrorMsg(data.error || 'Failed to start scan')
        setPhase('error')
        playSound('error')
        return
      }
      setJobId(data.job_id)
    } catch (e) {
      setErrorMsg(e.message)
      setPhase('error')
      playSound('error')
    }
  }

  const cancelScan = async () => {
    if (!jobId) return
    playSound('boop')
    try {
      await fetch(`${API_URL}/iso-scan/${jobId}/cancel`, { method: 'POST' })
    } catch (_) {}
  }

  const toggleSkin = (key) => {
    const next = new Set(selected)
    if (next.has(key)) next.delete(key); else next.add(key)
    setSelected(next)
  }

  const toggleAllForChar = (char) => {
    const skins = characters[char] || []
    const allSelected = skins.every(s => selected.has(s.key))
    const next = new Set(selected)
    if (allSelected) {
      for (const s of skins) next.delete(s.key)
    } else {
      for (const s of skins) next.add(s.key)
    }
    setSelected(next)
  }

  const toggleExpand = (char) => {
    const next = new Set(expanded)
    if (next.has(char)) next.delete(char); else next.add(char)
    setExpanded(next)
  }

  const selectAll = () => {
    const next = new Set()
    for (const skins of Object.values(characters)) {
      for (const s of skins) next.add(s.key)
    }
    setSelected(next)
  }

  const selectNone = () => setSelected(new Set())

  const importSelected = async () => {
    if (!selected.size || !jobId) return
    playSound('start')
    setPhase('importing')
    try {
      const res = await fetch(`${API_URL}/iso-scan/${jobId}/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keys: Array.from(selected), auto_fix: true }),
      })
      const data = await res.json()
      setImportResult(data)
      if (data.success) {
        await cleanupJob(jobId)
        setJobId(null)
      }
      setPhase('done')
      playSound(data.imported > 0 ? 'achievement' : 'error')
      if (onRefresh) await onRefresh()
    } catch (e) {
      setErrorMsg(e.message)
      setPhase('error')
      playSound('error')
    }
  }

  const cleanupJob = async (id = jobId) => {
    if (!id) return
    try { await fetch(`${API_URL}/iso-scan/${id}`, { method: 'DELETE' }) } catch (_) {}
  }

  const cleanup = async () => cleanupJob(jobId)

  const handleClose = async () => {
    playSound('boop')
    await cleanup()
    onClose && onClose()
  }

  const totalNew = Object.values(characters).reduce((n, arr) => n + arr.length, 0)
  const selectedCount = selected.size

  const customSummaryBlock = customSummary && (
    <div className="iso-scan-custom-summary">
      {[['characters', 'Custom characters'], ['stages', 'Custom stages']].map(([key, label]) => {
        const s = customSummary[key]
        if (!s) return null
        return (
          <div key={key} className="iso-scan-custom-summary-row">
            <strong>{label}:</strong>{' '}
            {s.imported.length
              ? `imported ${s.imported.join(', ')}`
              : 'nothing new found'}
            {s.skipped.length > 0 && ` · ${s.skipped.length} already in vault`}
            {s.errors.length > 0 && (
              <span className="iso-scan-custom-summary-error"> · {s.errors.join(' · ')}</span>
            )}
          </div>
        )
      })}
    </div>
  )

  // ─── Render ───────────────────────────────────────────────

  return (
    <div className="edit-modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) handleClose() }}>
      <div className="edit-modal-content iso-scan-modal" onClick={(e) => e.stopPropagation()}>
        {phase === 'idle' && (
          <>
            <h2>Scan ISOs</h2>

            {witAvailable === false && targets.skins && (
              <div className="iso-scan-warning">
                <strong>wit.exe missing.</strong>
                <p>
                  Place <code>wit-v3.05a-r8638-cygwin64</code> in <code>tools/</code> under
                  the project root. Download:{' '}
                  <span className="iso-scan-link">https://wit.wiimm.de/</span>
                </p>
              </div>
            )}

            <p className="iso-scan-help">
              Pick one or more <code>.iso</code> files and what to scan them for.
              Skins are compared against your vault + vanilla assets and shown as
              thumbnails so you pick which to keep; custom m-ex characters and
              stages are extracted straight into the vault.
            </p>

            <div className="iso-scan-targets">
              <label onMouseEnter={playHoverSound}>
                <input
                  type="checkbox"
                  checked={targets.skins}
                  onChange={() => { playSound('boop'); toggleTarget('skins') }}
                />
                Character skins
              </label>
              <label onMouseEnter={playHoverSound} title="Extract added m-ex fighters (slower: builds a temp project per ISO)">
                <input
                  type="checkbox"
                  checked={targets.customCharacters}
                  onChange={() => { playSound('boop'); toggleTarget('customCharacters') }}
                />
                Custom characters
              </label>
              <label onMouseEnter={playHoverSound} title="Extract added m-ex stages (slower: builds a temp project per ISO)">
                <input
                  type="checkbox"
                  checked={targets.customStages}
                  onChange={() => { playSound('boop'); toggleTarget('customStages') }}
                />
                Custom stages
              </label>
            </div>

            <div className="iso-scan-file-list">
              {isoPaths.length === 0 && (
                <div className="iso-scan-empty">No ISOs selected.</div>
              )}
              {isoPaths.map(p => (
                <div key={p} className="iso-scan-file-row">
                  <span className="iso-scan-file-name" title={p}>
                    {p.split(/[\\/]/).pop()}
                  </span>
                  <button
                    className="iso-scan-remove"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('boop'); removeIso(p) }}
                    title="Remove"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>

            <div className="edit-buttons iso-scan-actions">
              <button
                className="btn-cancel"
                onMouseEnter={playHoverSound}
                onClick={pickFiles}
                disabled={!window.electron}
              >
                + Add ISOs
              </button>
              <button
                className="btn-save"
                onMouseEnter={playHoverSound}
                onClick={startScan}
                disabled={!isoPaths.length || !anyTarget || (targets.skins && !witAvailable)}
              >
                Start scan ({isoPaths.length})
              </button>
              <button
                className="btn-cancel"
                onMouseEnter={playHoverSound}
                onClick={handleClose}
              >
                Close
              </button>
            </div>
          </>
        )}

        {phase === 'scanning' && (
          <>
            <h2>Scanning ISOs…</h2>
            <div className="export-progress" style={{ paddingBottom: 0 }}>
              <HexagonLoader
                className="progress-loader"
                size={112}
                label={PHASE_LABEL[progress.status] || 'Scanning'}
                progress={progress.percent > 0 ? progress.percent : null}
              />
              <div className="hexagon-progress-copy">
                <h3>{PHASE_LABEL[progress.status] || 'Scanning'}</h3>
                <p className="progress-message">{progress.message || '…'}</p>
              </div>
            </div>
            {stats && (
              <div className="iso-scan-live-stats">
                <span>{stats.existing} in vault</span>
                <span>·</span>
                <span>{stats.vanilla} vanilla</span>
                <span>·</span>
                <span>{stats.dupes} dupes</span>
                <span>·</span>
                <span>{stats.slippi_matched} slippi-matched</span>
              </div>
            )}
            <div className="edit-buttons">
              <button className="btn-cancel" onMouseEnter={playHoverSound} onClick={cancelScan}>
                Cancel
              </button>
            </div>
          </>
        )}

        {phase === 'custom-done' && (
          <>
            <h2 style={{ color: 'var(--color-success)' }}>Extraction complete</h2>
            {customSummaryBlock}
            <div className="edit-buttons">
              <button className="btn-save" onMouseEnter={playHoverSound} onClick={handleClose}>
                Done
              </button>
            </div>
          </>
        )}

        {phase === 'results' && (
          <>
            <h2>Scan complete — {totalNew} new skin{totalNew === 1 ? '' : 's'}</h2>
            {customSummaryBlock}

            <div className="iso-scan-toolbar">
              <button className="iso-scan-mini" onMouseEnter={playHoverSound}
                      onClick={() => { playSound('boop'); selectAll() }}>
                Select all
              </button>
              <button className="iso-scan-mini" onMouseEnter={playHoverSound}
                      onClick={() => { playSound('boop'); selectNone() }}>
                Select none
              </button>
              <div className="iso-scan-toolbar-spacer" />
              <span className="iso-scan-counter">
                {selectedCount} / {totalNew} selected
              </span>
            </div>

            <div className="iso-scan-results">
              {Object.entries(characters)
                .sort((a, b) => a[0].localeCompare(b[0]))
                .map(([char, skins]) => {
                  const isExpanded = expanded.has(char)
                  const charSelected = skins.filter(s => selected.has(s.key)).length
                  const allChar = charSelected === skins.length
                  const someChar = charSelected > 0 && charSelected < skins.length
                  return (
                    <div key={char} className="iso-scan-char-section">
                      <div className="iso-scan-char-header">
                        <button
                          className="iso-scan-collapse"
                          onClick={() => { playSound('boop'); toggleExpand(char) }}
                          onMouseEnter={playHoverSound}
                          title={isExpanded ? 'Collapse' : 'Expand'}
                        >
                          {isExpanded ? '▾' : '▸'}
                        </button>
                        <span className="iso-scan-char-name">{char}</span>
                        <span className="iso-scan-char-count">
                          {charSelected}/{skins.length}
                        </span>
                        <button
                          className="iso-scan-mini"
                          onMouseEnter={playHoverSound}
                          onClick={() => { playSound('boop'); toggleAllForChar(char) }}
                        >
                          {allChar ? 'none' : someChar ? 'all' : 'all'}
                        </button>
                      </div>
                      {isExpanded && (
                        <div className="iso-scan-csp-grid">
                          {skins.map(skin => {
                            const checked = selected.has(skin.key)
                            return (
                              <button
                                key={skin.key}
                                type="button"
                                className={`iso-scan-csp-tile ${checked ? 'selected' : ''}`}
                                onClick={() => { playSound('boop'); toggleSkin(skin.key) }}
                                onMouseEnter={playHoverSound}
                                title={`${skin.costume_code}\nfrom ${skin.source_iso}\nhash ${skin.dat_hash}`}
                              >
                                {skin.csp_url ? (
                                  <img
                                    src={`${BACKEND_URL}${skin.csp_url}`}
                                    alt={skin.costume_code}
                                    loading="lazy"
                                    draggable={false}
                                  />
                                ) : (
                                  <div className="iso-scan-no-csp">no preview</div>
                                )}
                                <div className="iso-scan-tile-check">
                                  {checked ? '✓' : ''}
                                </div>
                                <div className="iso-scan-tile-caption">
                                  {skin.costume_code}
                                </div>
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  )
                })}
            </div>

            {stats && (
              <div className="iso-scan-stats-bar">
                Skipped:&nbsp;
                <strong>{stats.existing}</strong> existing&nbsp;·&nbsp;
                <strong>{stats.vanilla}</strong> vanilla&nbsp;·&nbsp;
                <strong>{stats.dupes}</strong> dupes&nbsp;·&nbsp;
                <strong>{stats.slippi_matched}</strong> slippi-matched&nbsp;·&nbsp;
                <strong>{stats.data_mod}</strong> data&nbsp;mods
                {stats.custom_fighter > 0 && (
                  <>&nbsp;·&nbsp;<strong>{stats.custom_fighter}</strong> custom-fighter&nbsp;files</>
                )}
              </div>
            )}

            <div className="edit-buttons iso-scan-actions">
              <button className="btn-cancel" onMouseEnter={playHoverSound} onClick={handleClose}>
                Cancel
              </button>
              <button
                className="btn-save"
                onMouseEnter={playHoverSound}
                onClick={importSelected}
                disabled={!selectedCount}
              >
                Import {selectedCount} selected
              </button>
            </div>
          </>
        )}

        {phase === 'importing' && (
          <>
            <h2>Importing…</h2>
            <div className="export-progress" style={{ paddingBottom: 0 }}>
              <HexagonLoader className="progress-loader" size={112} label="Importing" progress={null} />
              <div className="hexagon-progress-copy">
                <h3>Adding {selectedCount} skin{selectedCount === 1 ? '' : 's'} to your vault…</h3>
                <p className="progress-message">This may take a moment.</p>
              </div>
            </div>
          </>
        )}

        {phase === 'done' && importResult && (
          <>
            <h2 style={{ color: 'var(--color-success)' }}>
              Imported {importResult.imported} / {importResult.total_selected}
            </h2>
            <div style={{ textAlign: 'center', padding: '1rem 0' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✓</div>
              {importResult.errors && importResult.errors.length > 0 && (
                <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
                  {importResult.errors.length} skin(s) failed to import.
                </p>
              )}
            </div>
            <div className="edit-buttons">
              <button className="btn-save" onMouseEnter={playHoverSound} onClick={handleClose}>
                Done
              </button>
            </div>
          </>
        )}

        {phase === 'error' && (
          <>
            <h2 style={{ color: 'var(--color-error)' }}>Scan failed</h2>
            <div style={{ textAlign: 'center', padding: '1rem 0' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem', color: 'var(--color-error)' }}>✕</div>
              <p style={{ color: 'var(--color-error)' }}>{errorMsg}</p>
            </div>
            <div className="edit-buttons">
              <button className="btn-cancel" onMouseEnter={playHoverSound} onClick={handleClose}>
                Close
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
