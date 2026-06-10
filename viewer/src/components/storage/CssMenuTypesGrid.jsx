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
  },
  {
    key: 'doors',
    name: 'Doors',
    short: 'DR',
    description: 'Character port door textures'
  }
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
            <p className="menu-type-desc">{modType.description}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
