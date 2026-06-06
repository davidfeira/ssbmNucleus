import React from 'react';
import ProgressPanel from './ProgressPanel';
import { getProgressMessage } from '../shared/progressText';

const TEST_VERDICT_LABEL = {
  healthy: 'PASS',
  ended: 'PASS — match ended',
  never_started: 'DID NOT START',
  hung: 'HUNG',
  crashed: 'CRASH',
  error: 'ERROR',
};

/**
 * Boots the exported ISO in a throwaway Dolphin, plays a short automated match
 * to verify the mods load, and reports PASS / CRASH with a screenshot. The
 * user's own Slippi setup is untouched and it never goes online.
 */
const TestInGamePanel = ({
  testing,
  testProgress,
  testStage,
  testMessage,
  testResult,
  testError,
  slippiPath,
  manifestPath,
  setManifestPath,
  showTestAdvanced,
  setShowTestAdvanced,
  onTest,
}) => {
  if (testing) {
    return (
      <ProgressPanel
        title="Testing in game…"
        label="In-game test progress"
        progressValue={testProgress > 0 ? testProgress : null}
        metaText={testStage ? testStage.replace(/_/g, ' ') : null}
        messageText={getProgressMessage(testMessage, 'Booting an isolated Dolphin…')}
      />
    );
  }

  if (testResult) {
    const r = testResult;
    const pass = !!r.success;
    const headline = pass
      ? '✓ PASS'
      : `✕ ${TEST_VERDICT_LABEL[r.verdict] || String(r.verdict || '').toUpperCase()}`;
    return (
      <div className="test-result" style={{ textAlign: 'center' }}>
        <div className={`test-verdict-badge ${pass ? 'pass' : 'fail'}`}>{headline}</div>
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
            style={{
              maxWidth: '100%', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)', marginBottom: '1rem',
            }}
          />
        )}
        {Array.isArray(r.checks) && r.checks.length > 0 && (
          <ul className="test-checks">
            {r.checks.map((c, i) => {
              const ok = c.verdict === 'healthy';
              return (
                <li key={i}>
                  <span className={`check-mark ${ok ? 'ok' : 'bad'}`}>{ok ? '✓' : '✕'}</span>
                  <span style={{ color: 'var(--color-text-primary)' }}>{c.label}</span>
                  {Array.isArray(c.covers) && c.covers.length > 0 && (
                    <span className="check-covers">[{c.covers.join(', ')}]</span>
                  )}
                  {!ok && c.reason && <div className="check-reason">{c.reason}</div>}
                </li>
              );
            })}
          </ul>
        )}
        <button className="btn-secondary" onClick={onTest} disabled={!slippiPath}>
          Test again
        </button>
      </div>
    );
  }

  if (testError) {
    return (
      <div className="test-error" style={{ textAlign: 'center' }}>
        <p style={{ color: 'var(--color-error, #e74c3c)' }}>Test failed: {testError}</p>
        <button className="btn-secondary" onClick={onTest} disabled={!slippiPath}>
          Try again
        </button>
      </div>
    );
  }

  return (
    <>
      <h4 className="action-heading">Test in game</h4>
      <p className="action-blurb">
        Boots this ISO in a throwaway Dolphin, plays a short automated match to verify your
        mods load, and reports PASS / CRASH with a screenshot. Your own Slippi setup is
        untouched, and it never goes online.
      </p>
      {!slippiPath && <p className="card-warning">Set the Slippi path in Settings first.</p>}
      <button
        className="btn-export"
        style={{ width: '100%' }}
        onClick={onTest}
        disabled={!slippiPath}
      >
        🎮 Test in game
      </button>
      <button
        className="advanced-toggle"
        style={{ marginTop: '0.5rem' }}
        onClick={() => setShowTestAdvanced(!showTestAdvanced)}
      >
        <span className="toggle-arrow">{showTestAdvanced ? '▼' : '▶'}</span>
        Drive specific mods (optional)
      </button>
      {showTestAdvanced && (
        <div style={{ marginTop: '0.5rem' }}>
          <label className="manifest-label">
            Build manifest path — a JSON file describing which character / stage / effect to
            drive. Leave blank to just boot and watch for a crash.
          </label>
          <input
            type="text"
            value={manifestPath}
            onChange={(e) => setManifestPath(e.target.value)}
            placeholder="C:\\...\\last-build.json"
            className="manifest-input"
          />
        </div>
      )}
    </>
  );
};

export default TestInGamePanel;
