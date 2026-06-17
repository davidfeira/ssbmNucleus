/**
 * DiscUsageIndicator — build-capacity meter for the install-page header.
 *
 * There are TWO independent limits, shown as two stacked rows:
 *
 *  1. COSTUME COUNT (primary) — the character-select screen HANGS once a build
 *     holds more than ~512 TOTAL costumes across the whole roster. This is the
 *     ceiling you actually hit first, it's a hard game limit, and it is
 *     INDEPENDENT of disc size and of HD-texture mode — freeing disc space does
 *     NOT raise it. Verified in-game with video stripped (so size was a non-
 *     factor): count-500 ran at 60 fps, count-550 froze at the CSS. See
 *     docs/MEX_BUILD_LIMITS.md. Driven purely by the `totalCostumes` prop, so it
 *     shows even if the disc-usage fetch fails.
 *
 *  2. DISC SIZE (secondary) — a GameCube disc holds 1,459,978,240 bytes. A build
 *     over that still RUNS in Dolphin, but won't boot on real hardware / an SD
 *     setup. Shown as a stacked breakdown of what fills the disc (hover a
 *     segment), with an optional "Free space" tool that strips the big vanilla
 *     video files (~810 MB). Stripping frees DISC space — it does not raise the
 *     costume-count ceiling. Driven by GET /project/disc-usage.
 */
import React, { useEffect, useState } from 'react'

// Costume-count gauge. The CSS hang is a CSP-texture-MEMORY limit, not a fixed count:
// the screen freezes when CSP video memory (128+total)*r^2 overflows the heap. The app
// AUTO-compresses CSP portraits as you add costumes (calculate_auto_compression scales
// the ratio r from 1.0 down toward 0.1), so a normally-exported build is safe up to
// ~1150 total (where even max compression can't fit). (An UNcompressed export walls at
// only ~510 — the app compresses for you.) See docs/MEX_BUILD_LIMITS.md §2.
const COSTUME_HANG = 1150   // ~ceiling once CSPs are auto-compressed (CSS-memory bound)

// Disc size has TWO thresholds. The console disc (from the backend = 1,459,978,240 B)
// is the real-hardware / SD limit. A build over it still RUNS in Dolphin (confirmed
// to +968 MiB over); Dolphin only stops booting once the ISO passes ~4 GiB = 2^32 —
// the GameCube image format's 32-bit byte offsets. See docs/MEX_BUILD_LIMITS.md §3.
const DOLPHIN_LIMIT = 4 * 1024 * 1024 * 1024   // ~4 GiB ISO-format ceiling

// Drawn left-to-right; costumes last so added skins sit by the free-space edge.
// Video is the big strippable chunk.
const CATEGORIES = [
  { key: 'video', label: 'Video', color: '#566270', strip: true, note: 'cutscenes / demos' },
  { key: 'audio', label: 'Audio', color: '#7a5bbf' },
  // Trophies (Ty*) are NOT strippable: MexManager's TrophyLoader reads them when the
  // project opens, so deleting them breaks the workspace. Shown, not removable.
  { key: 'trophies', label: 'Trophies', color: '#8a7b4f' },
  { key: 'stages', label: 'Stages', color: '#3f8f5f' },
  { key: 'other', label: 'Other', color: '#455160' },
  { key: 'costumes', label: 'Costumes', color: '#c8503f' },
]
const STRIPPABLE = CATEGORIES.filter((c) => c.strip)

const fmtGB = (b) => `${(b / 1e9).toFixed(2)} GB`
const fmtMB = (b) => `${Math.round(b / 1e6)} MB`
// Remaining-space readout: GB once it's ≥ ~1 GB, else MB — keeps both bars legible.
const fmtSpace = (b) => (b >= 1e9 ? fmtGB(b) : fmtMB(b))

export default function DiscUsageIndicator({ API_URL, projectLoaded, totalCostumes = 0 }) {
  const [data, setData] = useState(null)
  const [hovered, setHovered] = useState(null)
  const [stripOpen, setStripOpen] = useState(false)
  const [selected, setSelected] = useState({})
  const [busy, setBusy] = useState(false)
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    if (!projectLoaded) return undefined
    let cancelled = false
    fetch(`${API_URL}/project/disc-usage`)
      .then((r) => r.json())
      .then((d) => { if (cancelled) return; setData(d && d.success ? d : null) })
      .catch(() => { if (!cancelled) setData(null) })
    return () => { cancelled = true }
  }, [API_URL, projectLoaded, totalCostumes, nonce])

  if (!projectLoaded) return null

  // ── Secondary limit: disc size (real-hardware ceiling; Dolphin tolerates over) ──
  const disc = data
    ? (() => {
      const { capacity, used, free, breakdown } = data
      const pct = (b) => `${Math.max(0, Math.min(100, (b / capacity) * 100))}%`
      const overConsole = used > capacity
      const overConsoleBy = used - capacity            // bytes past the console disc
      const overDolphin = used > DOLPHIN_LIMIT
      const dolphinFree = DOLPHIN_LIMIT - used         // headroom before the ISO won't boot
      // How many more costumes fit in each free space, capped by the CSS-memory ceiling
      // (so we never promise more than the game can actually load).
      const avg = data.avgSkinBytes || 497 * 1024      // ~bytes per added costume on disc
      const memRoom = Math.max(0, COSTUME_HANG - totalCostumes)
      const consoleFits = Math.min(Math.floor(free / avg), memRoom)
      const dolphinFits = Math.min(Math.floor(dolphinFree / avg), memRoom)
      const anyStrippable = STRIPPABLE.some((c) => (breakdown[c.key] || 0) > 0)
      const selectedBytes = STRIPPABLE.reduce(
        (s, c) => s + (selected[c.key] ? breakdown[c.key] || 0 : 0), 0)
      const hov = hovered ? CATEGORIES.find((c) => c.key === hovered) : null
      return { capacity, used, free, breakdown, pct, overConsole, overConsoleBy,
        overDolphin, dolphinFree, consoleFits, dolphinFits, anyStrippable, selectedBytes, hov }
    })()
    : null

  const doStrip = async () => {
    const targets = STRIPPABLE.filter((c) => selected[c.key]).map((c) => c.key)
    if (!targets.length) return
    setBusy(true)
    try {
      const res = await fetch(`${API_URL}/project/strip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targets }),
      }).then((r) => r.json())
      if (res.success) { setStripOpen(false); setSelected({}); setNonce((n) => n + 1) }
    } finally { setBusy(false) }
  }

  return (
    <div className="disc-usage">
      {/* Two disc bars (console + Dolphin): each shows free space and ~how many more costumes fit */}
      {disc && (
        <div className="disc-usage__section">
          {/* CONSOLE bar: build composition, full width = the 1.46 GB console disc */}
          <div
            className="disc-usage__gauge"
            title="Real GameCube / SD-console disc (1.46 GB). A build past the end of this bar won't boot on hardware — but still runs in Dolphin."
          >
            <span className="disc-usage__gauge-label">Console</span>
            <div className="disc-usage__barwrap">
              {disc.hov && (
                <div className="disc-usage__tip">
                  <span className="disc-usage__dot" style={{ background: disc.hov.color }} />
                  {disc.hov.label}: {fmtMB(disc.breakdown[disc.hov.key])} (
                  {Math.round((disc.breakdown[disc.hov.key] / disc.capacity) * 100)}%)
                  {disc.hov.strip ? ' · removable' : ''}
                </div>
              )}
              <div className={`disc-usage__bar${disc.overConsole ? ' is-over' : ''}`}>
                {CATEGORIES.map((c) => (disc.breakdown[c.key] > 0 ? (
                  <span
                    key={c.key}
                    className="disc-usage__seg"
                    style={{ width: disc.pct(disc.breakdown[c.key]), background: c.color }}
                    title={`${c.label}: ${fmtMB(disc.breakdown[c.key])}`}
                    onMouseEnter={() => setHovered(c.key)}
                    onMouseLeave={() => setHovered((h) => (h === c.key ? null : h))}
                  />
                ) : null))}
              </div>
            </div>
            <span className={`disc-usage__gauge-val ${disc.overConsole ? 'is-over' : 'is-ok'}`}>
              {disc.overConsole
                ? `${fmtMB(disc.overConsoleBy)} over`
                : `${fmtSpace(disc.free)} free · ~${disc.consoleFits} costumes`}
            </span>
          </div>

          {/* DOLPHIN bar: build size, full width = the ~4 GiB ISO boot ceiling */}
          <div
            className="disc-usage__gauge"
            title="Dolphin / ISO-format ceiling (~4 GiB = 2³²). Dolphin runs an over-disc build up to here; past the end of this bar the ISO won't boot at all."
          >
            <span className="disc-usage__gauge-label">Dolphin</span>
            <div className="disc-usage__barwrap">
              <div className="disc-usage__bar">
                <span
                  className={`disc-usage__dolfill ${disc.overDolphin ? 'is-fatal' : 'is-ok'}`}
                  style={{ width: `${Math.max(2, Math.min(100, (disc.used / DOLPHIN_LIMIT) * 100))}%` }}
                />
              </div>
            </div>
            <span className={`disc-usage__gauge-val ${disc.overDolphin ? 'is-fatal' : 'is-ok'}`}>
              {disc.overDolphin
                ? 'won’t boot'
                : `${fmtSpace(disc.dolphinFree)} free · ~${disc.dolphinFits} costumes`}
            </span>
          </div>

          {disc.anyStrippable && (
            <button
              type="button"
              className="disc-usage__free-btn"
              onClick={() => setStripOpen((o) => !o)}
              title="Remove vanilla videos to free disc space (for real-hardware / SD builds)"
            >
              Free space ▾
            </button>
          )}

          {stripOpen && (
            <div className="disc-usage__strip">
              <div className="disc-usage__strip-title">Remove vanilla content to free disc space</div>
              {STRIPPABLE.map((c) => (disc.breakdown[c.key] > 0 ? (
                <label key={c.key} className="disc-usage__strip-row">
                  <input
                    type="checkbox"
                    checked={!!selected[c.key]}
                    onChange={(e) => setSelected((s) => ({ ...s, [c.key]: e.target.checked }))}
                  />
                  <span className="disc-usage__dot" style={{ background: c.color }} />
                  <span className="disc-usage__strip-label">{c.label}</span>
                  <span className="disc-usage__strip-size">{fmtMB(disc.breakdown[c.key])}</span>
                </label>
              ) : null))}
              <div className="disc-usage__strip-note">
                Frees disc space for real-hardware / SD builds (Dolphin runs over-disc fine). Does
                NOT raise the ~{COSTUME_HANG}-costume limit above. Permanent for this project
                (rebuild from a vanilla ISO to restore); only removes the intro movie / cutscenes
                and idle demo, not VS matches.
              </div>
              <div className="disc-usage__strip-actions">
                <button type="button" className="disc-usage__strip-cancel"
                  onClick={() => { setStripOpen(false); setSelected({}) }}>
                  Cancel
                </button>
                <button type="button" className="disc-usage__strip-go" disabled={busy || disc.selectedBytes === 0}
                  onClick={doStrip}>
                  {busy ? 'Removing…' : disc.selectedBytes ? `Free up ${fmtMB(disc.selectedBytes)}` : 'Select to remove'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
