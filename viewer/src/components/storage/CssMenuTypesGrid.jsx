/**
 * CssMenuTypesGrid - Mod type selector for the Character Select Screen.
 *
 * Currently exposes one tile: Icon Grid. Additional CSS mod types
 * (layouts, backgrounds, portraits, etc.) can be added here later.
 */
import { playSound, playHoverSound } from '../../utils/sounds'

const CSS_MOD_TYPES = [
  {
    key: 'icon_grid',
    name: 'Icon Grid',
    short: 'IG',
    description: 'Custom character portraits used on the CSS banner'
  },
  {
    key: 'background',
    name: 'Background',
    short: 'BG',
    description: 'CSS background and stage art'
  }
]

export default function CssMenuTypesGrid({ onSelectModType }) {
  return (
    <div className="grid-wrapper">
      <div className="stages-grid">
        {CSS_MOD_TYPES.map((modType) => (
          <div
            key={modType.key}
            className="stage-card"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); onSelectModType(modType.key) }}
          >
            <div className="stage-icon-container">
              <div className="stage-placeholder" style={{ display: 'flex' }}>
                {modType.short}
              </div>
            </div>

            <div className="stage-info">
              <h3 className="stage-name">{modType.name}</h3>
              <p className="stage-variant-count">{modType.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
