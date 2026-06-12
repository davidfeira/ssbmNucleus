/**
 * InGameTestPanel - inline "Test in game" button + progress/result panel.
 *
 * Used by the custom character / custom stage detail views (which aren't modals).
 * Pass a useInGameTest() instance as `test` and an `onStart` handler. Mirrors the
 * costume modal's overlay: a button -> live progress -> PASS/CRASH result with a
 * screenshot and per-check checklist.
 */

import DolphinEmbedPanel from './DolphinEmbedPanel'
import HexagonLoader from './HexagonLoader'

const VERDICT_LABEL = {
  healthy: 'PASS',
  ended: 'PASS — match ended',
  never_started: 'DID NOT START',
  hung: 'HUNG',
  crashed: 'CRASH',
  error: 'ERROR',
}

export default function InGameTestPanel({ test, onStart, label = 'Test in Game', disabled = false }) {
  const { testingInGame, testStatus, testResult, testError, testMode, resetTest } = test

  if (testingInGame) {
    return (
      <div style={{ textAlign: 'center', padding: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.75rem' }}>
          <HexagonLoader
            size={88}
            label="Testing in game"
            progress={Number.isFinite(testStatus?.percentage) ? testStatus.percentage : null}
            centerLabel={`${Math.round(testStatus?.percentage || 0)}%`}
            minimumVisibleProgress={4}
          />
        </div>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
          {testStatus?.message || 'Working…'}
        </p>
        {/* Embedded for tests AND captures (shots are grabbed via PrintWindow
            at the embedded size — a small resolution trade for not having a
            floating Dolphin window over the app). */}
        <DolphinEmbedPanel active />
        <p style={{ fontSize: '0.8em', color: 'var(--color-text-secondary)', marginTop: '0.75rem' }}>
          Builds a one-mod ISO and plays a short match in a throwaway Dolphin.
          Your Slippi setup is untouched, and it never goes online.
        </p>
      </div>
    )
  }

  if (testError) {
    return (
      <div style={{ textAlign: 'center', padding: '1rem' }}>
        <p style={{ color: 'var(--color-error, #e74c3c)', marginBottom: '0.75rem' }}>Test failed: {testError}</p>
        <button className="btn-secondary" onClick={resetTest}>Close</button>
      </div>
    )
  }

  if (testResult) {
    const r = testResult
    return (
      <div style={{ textAlign: 'center', padding: '1rem' }}>
        <div style={{
          display: 'inline-block', padding: '0.35rem 1.1rem', borderRadius: 'var(--radius-md)',
          fontWeight: 700, fontSize: '1.15em', marginBottom: '0.75rem', color: '#fff',
          background: r.success ? 'var(--color-success, #2ecc71)' : 'var(--color-error, #e74c3c)'
        }}>
          {r.success ? '✓ PASS' : `✕ ${VERDICT_LABEL[r.verdict] || String(r.verdict || '').toUpperCase()}`}
        </div>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>{r.reason}</p>
        {r.onlineAborted && (
          <p style={{ color: 'var(--color-warning, #f39c12)', marginBottom: '1rem' }}>
            Stopped before going online — no matchmaking occurred.
          </p>
        )}
        {r.screenshot && (
          <img
            src={r.screenshot}
            alt="In-game screenshot"
            style={{ maxWidth: '100%', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', marginBottom: '1rem' }}
          />
        )}
        {Array.isArray(r.checks) && r.checks.length > 0 && (
          <ul style={{ listStyle: 'none', padding: 0, textAlign: 'left', maxWidth: 480, margin: '0 auto 1rem' }}>
            {r.checks.map((c, i) => {
              const ok = c.verdict === 'healthy'
              return (
                <li key={i} style={{ padding: '0.4rem 0', borderBottom: '1px solid var(--color-border)' }}>
                  <span style={{ color: ok ? 'var(--color-success, #2ecc71)' : 'var(--color-error, #e74c3c)', marginRight: '0.5rem', fontWeight: 700 }}>
                    {ok ? '✓' : '✕'}
                  </span>
                  <span style={{ color: 'var(--color-text-primary)' }}>{c.label}</span>
                  {!ok && c.reason && (
                    <div style={{ fontSize: '0.8em', color: 'var(--color-text-secondary)', marginLeft: '1.5rem' }}>{c.reason}</div>
                  )}
                </li>
              )
            })}
          </ul>
        )}
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
          <button className="btn-export" onClick={onStart} disabled={disabled}>Test again</button>
          <button className="btn-secondary" onClick={resetTest}>Close</button>
        </div>
      </div>
    )
  }

  return (
    <button
      className="btn-export"
      onClick={onStart}
      disabled={disabled}
      title="Build a one-mod test ISO and play a short match to verify it loads"
    >
      🎮 {label}
    </button>
  )
}
