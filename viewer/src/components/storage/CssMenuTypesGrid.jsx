/**
 * CssMenuTypesGrid - Mod type selector for the Character Select Screen.
 *
 * Currently exposes one tile: Icon Grid. Additional CSS mod types
 * (layouts, backgrounds, portraits, etc.) can be added here later.
 */
import { playSound, playHoverSound } from '../../utils/sounds'

const CSS_MOD_TYPES = [
  { key: 'icon_grid', name: 'Icon Grid', short: 'IG' },
  { key: 'background', name: 'Background', short: 'BG' },
  { key: 'doors', name: 'Doors', short: 'DR' }
]

export default function CssMenuTypesGrid({ onSelectModType }) {
  return (
    <div className="stages-grid">
      {CSS_MOD_TYPES.map((modType) => (
        <div
          key={modType.key}
          className="stage-card"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); onSelectModType(modType.key) }}
        >
          <div className="stage-info menu-type-info">
            <h3 className="stage-name">{modType.name}</h3>
          </div>
        </div>
      ))}
    </div>
  )
}
