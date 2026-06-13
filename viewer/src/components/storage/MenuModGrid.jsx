/**
 * MenuModGrid - Unified vault grid for menu & HUD texture mods.
 *
 * Every CSS / SSS / HUD mod list (doors, backgrounds, icon grids, pause
 * screens, percent fonts) renders through this so they share ONE polished
 * card shell — the same one the Fighters and Stages grids use (framed
 * thumbnail, LED hover border, centered title + meta, and the big hover
 * pencil). The pencil opens the per-mod edit modal (MenuModEditModal); the
 * old per-card action overlay now lives inside that modal, matching the
 * costume / stage edit flow.
 *
 * Per-list behavior is supplied through props rather than forked markup:
 *   - thumb / imgFit    frame shape + how the texture fills it (doors stretch
 *                       to 128x200 to mirror the in-game door exactly)
 *   - onEditClick       opens the edit modal (renders the hover pencil)
 *   - onCardClick       optional whole-card navigation (e.g. icon grid detail)
 *   - createCard        trailing "new from scratch" gateway card
 */
import { playSound, playHoverSound } from '../../utils/sounds'
import { BACKEND_URL } from '../../config'

export default function MenuModGrid({
  mods = [],
  loading = false,
  emptyText,
  thumb = 'wide',                                   // 'wide' | 'tall' | 'square'
  imgFit = 'contain',                               // 'contain' | 'cover' | 'fill'
  getImageUrl = (m) => m.imageUrl || m.screenshotUrl || null,
  getMeta,                                          // (mod) => node | null
  onCardClick,                                      // (mod) => void
  onEditClick,                                      // (mod) => void  → hover pencil
  createCard,                                       // { label, title, onClick }
  cacheBust = 0,
}) {
  const thumbClass = `mmod-thumb mmod-thumb--${thumb} mmod-thumb--fit-${imgFit}`

  if (loading) {
    return (
      <div className="mmod-grid">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={`mmod-skel-${i}`} className="mmod-card mmod-card--skeleton">
            <div className={`${thumbClass} skeleton`} />
            <div className="skeleton skeleton-text" style={{ width: '55%', height: 12, margin: '0 auto' }} />
          </div>
        ))}
      </div>
    )
  }

  const isEmpty = mods.length === 0

  if (isEmpty && !createCard) {
    return <div className="vault-empty">{emptyText}</div>
  }

  return (
    <>
      {isEmpty && emptyText && <div className="vault-empty">{emptyText}</div>}
      <div className="mmod-grid">
        {mods.map((mod) => {
          const url = getImageUrl(mod)
          const src = url ? `${BACKEND_URL}${url}${cacheBust ? `?v=${cacheBust}` : ''}` : null
          const meta = getMeta?.(mod)
          return (
            <div
              key={mod.id}
              className={`stage-card mmod-card${onCardClick ? ' mmod-card--clickable' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={onCardClick ? () => { playSound('boop'); onCardClick(mod) } : undefined}
            >
              <div className={thumbClass}>
                {/* Monogram sits underneath; the image overlays it and reveals
                    it again if the screenshot fails to load. */}
                <span className="mmod-monogram">{(mod.name || '?')[0]}</span>
                {src && (
                  <img
                    src={src}
                    alt={mod.name}
                    onError={(e) => { e.target.style.visibility = 'hidden' }}
                  />
                )}

                {onEditClick && (
                  <button
                    className="btn-edit"
                    onMouseEnter={playHoverSound}
                    onClick={(e) => { e.stopPropagation(); playSound('boop'); onEditClick(mod) }}
                    title="Edit"
                  >
                    ✎
                  </button>
                )}
              </div>

              <div className="stage-info">
                <h3 className="stage-name" title={mod.name}>{mod.name}</h3>
                {meta && <p className="stage-variant-count">{meta}</p>}
              </div>
            </div>
          )
        })}

        {createCard && (
          <div
            className="stage-card mmod-card mmod-card--create"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); createCard.onClick() }}
            title={createCard.title}
          >
            <div className={thumbClass}>
              <span className="mmod-monogram mmod-monogram--plus">+</span>
            </div>
            <div className="stage-info">
              <h3 className="stage-name">{createCard.label}</h3>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
