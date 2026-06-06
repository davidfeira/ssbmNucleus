import React from 'react';
import ProgressPanel from './ProgressPanel';

/**
 * Manual texture-pack fallback: the user boots the ISO in Dolphin and scrolls
 * the CSS while the backend watches the dump folder and matches portraits live.
 * Kept for the rare cases the automatic namer can't cover (or by user choice).
 */
const ManualListenPanel = ({
  textureProgress,
  characters,
  currentCharIndex,
  setCurrentCharIndex,
  onDownload,
  onDone,
  onShowBundle,
}) => {
  const current = characters[currentCharIndex];

  return (
    <div className="listening-mode">
      <ProgressPanel
        title="Texture Pack — manual scan"
        label="Texture pack scan progress"
        progressValue={textureProgress.percentage > 0 ? textureProgress.percentage : null}
        messageText={`${textureProgress.matched} / ${textureProgress.total} textures matched`}
        metaText={
          characters.length > 0 && current
            ? `Current focus: ${current.name}`
            : 'Preparing scan targets…'
        }
        className="listening-progress-shell"
      />

      {characters.length > 0 && current && (
        <div className="current-character-section">
          <div className="current-char-header">
            <span className="current-label">
              {current.matched === current.total ? 'Complete!' : 'Scan next:'}
            </span>
            <span className="current-char-name">{current.name}</span>
          </div>
          <div className="costume-dots">
            {current.costumes.map((costume, i) => (
              <div
                key={i}
                className={`costume-dot ${costume.matched ? 'matched' : ''}`}
                title={`Costume ${costume.index + 1}`}
              />
            ))}
          </div>
          <p className="current-char-progress">
            {current.matched} / {current.total} costumes
            {current.matched === current.total && ' ✓'}
          </p>
        </div>
      )}

      <div className="character-list">
        <div className="char-list-header">All Characters</div>
        <div className="char-list-scroll">
          {characters.map((char, idx) => (
            <div
              key={char.name}
              className={`char-list-item ${idx === currentCharIndex ? 'current' : ''} ${
                char.matched === char.total ? 'complete' : ''
              } ${char.matched > 0 && char.matched < char.total ? 'partial' : ''}`}
              onClick={() => setCurrentCharIndex(idx)}
            >
              <span className="char-name">{char.name}</span>
              <span className="char-progress">
                {char.matched}/{char.total}
                {char.matched === char.total && ' ✓'}
              </span>
            </div>
          ))}
        </div>
      </div>

      <p className="listening-instructions">
        Open the ISO in Dolphin and scroll through each character’s costumes on the CSS.
        The view auto-updates as textures are matched.
      </p>

      <div className="listening-actions">
        <button className="btn-download" onClick={onDownload}>Download ISO</button>
        <button className="btn-done" onClick={onDone}>Done — Finish Texture Pack</button>
        <button
          className="btn-export-bundle"
          onClick={onShowBundle}
          style={{ background: 'var(--gradient-gold)' }}
        >
          Export as Bundle
        </button>
      </div>
    </div>
  );
};

export default ManualListenPanel;
