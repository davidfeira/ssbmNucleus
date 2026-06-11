/**
 * DolphinEmbedPanel - shows the live throwaway-Dolphin window INSIDE the app
 * while an in-game test runs.
 *
 * Same trick as EmbeddedModelViewer: this is just a placeholder div -- the
 * backend strips the Dolphin render window's title bar and SetWindowPos-es it
 * (always-on-top, never activated) over this rect, so the game appears to play
 * in the panel. We poll our own screen rect (catches app-window moves, which
 * have no DOM event) and park the native window offscreen when hidden. The
 * render window only exists once the game starts booting, so we keep polling
 * with a "found: false" loader through the build phase.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { API_URL } from '../../config'

export default function DolphinEmbedPanel({ active, fill = false }) {
  const placeholderRef = useRef(null)
  const lastSentRef = useRef(null)   // JSON key of the last acknowledged post
  const busyRef = useRef(false)      // one request in flight at a time
  const foundRef = useRef(false)
  const tickRef = useRef(0)
  const [found, setFound] = useState(false)

  const sendPosition = useCallback(async () => {
    const el = placeholderRef.current
    if (!el || busyRef.current) return

    const rect = el.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 1

    let path, body
    if (rect.width < 2 || rect.height < 2) {
      // Collapsed / hidden mid-layout: get the native window out of the way.
      path = 'park'
      body = {}
    } else {
      // Screen rect in PHYSICAL pixels (same math as EmbeddedModelViewer):
      // window position + chrome height + element offset, all × devicePixelRatio.
      const screenLeft = window.screenLeft !== undefined ? window.screenLeft : window.screenX
      const screenTop = window.screenTop !== undefined ? window.screenTop : window.screenY
      const chromeHeight = window.outerHeight - window.innerHeight
      path = 'position'
      body = {
        x: Math.round((screenLeft + rect.left) * dpr),
        y: Math.round((screenTop + chromeHeight + rect.top) * dpr),
        width: Math.round(rect.width * dpr),
        height: Math.round(rect.height * dpr),
      }
    }

    // Until the window is found, retry every tick (Dolphin appears mid-test);
    // after that only on change, plus a ~2s heartbeat in case Dolphin recreated
    // its render window (fresh title bar, default position).
    const key = `${path}:${JSON.stringify(body)}`
    tickRef.current += 1
    if (foundRef.current && lastSentRef.current === key && tickRef.current % 8 !== 0) return

    busyRef.current = true
    try {
      const res = await fetch(`${API_URL}/test-in-game/window/${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      lastSentRef.current = key
      const ok = !!(data && data.found) && path === 'position'
      if (ok !== foundRef.current) {
        foundRef.current = ok
        setFound(ok)
      }
    } catch {
      // Backend busy/unreachable -- try again next tick.
    } finally {
      busyRef.current = false
    }
  }, [])

  useEffect(() => {
    if (!active) return undefined
    foundRef.current = false
    lastSentRef.current = null
    setFound(false)

    sendPosition()
    const intervalId = setInterval(sendPosition, 250)
    const handleMove = () => sendPosition()
    window.addEventListener('resize', handleMove)
    window.addEventListener('scroll', handleMove, true)
    return () => {
      clearInterval(intervalId)
      window.removeEventListener('resize', handleMove)
      window.removeEventListener('scroll', handleMove, true)
      foundRef.current = false
      // Best-effort: if the test Dolphin is still alive, move it offscreen.
      fetch(`${API_URL}/test-in-game/window/park`, { method: 'POST' }).catch(() => {})
    }
  }, [active, sendPosition])

  if (!active) return null

  const placeholder = (
    <div
      ref={placeholderRef}
      style={{
        aspectRatio: '4 / 3',
        // fill: contain-fit 4:3 inside the flex-given stage (100cqw/100cqh =
        // the stage's own size -- can never overflow, so nothing scrolls).
        // inline: scale with the viewport (cq units fall back to viewport
        // units with no container), ~17rem reserved for surrounding text.
        width: fill
          ? 'min(100cqw, calc(100cqh * 4 / 3))'
          : 'clamp(280px, calc((100cqh - 17rem) * 4 / 3), 100%)',
        margin: fill ? '0 auto' : '1rem auto 0',
        background: 'var(--color-bg-deep)',
        border: '1px solid var(--color-border-subtle)',
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {!found && (
        <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.85em', padding: '1rem', textAlign: 'center' }}>
          The game appears here once Dolphin boots…
        </p>
      )}
    </div>
  )

  if (!fill) return placeholder

  // The stage: takes whatever space the flex-column parent has left and
  // becomes the size container the placeholder fits into. minHeight: 0 lets
  // it actually shrink instead of forcing overflow.
  return (
    <div
      style={{
        flex: '1 1 auto', minHeight: 0, width: '100%', marginTop: '1rem',
        containerType: 'size',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
    >
      {placeholder}
    </div>
  )
}
