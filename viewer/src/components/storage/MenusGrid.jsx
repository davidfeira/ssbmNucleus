/**
 * MenusGrid - Menu type selector (CSS / SSS)
 *
 * Top-level grid of menu categories: Character Select Screen and Stage Select Screen.
 * Clicking a card calls onSelectMenuType with 'css' or 'sss'.
 */
import { playSound, playHoverSound } from '../../utils/sounds'

const MENU_TYPES = [
  {
    key: 'css',
    name: 'Character Select Screen',
    short: 'CSS',
    description: 'CSS layouts, backgrounds, and portrait mods'
  },
  {
    key: 'sss',
    name: 'Stage Select Screen',
    short: 'SSS',
    description: 'SSS layouts, backgrounds, and icon mods'
  }
]

export default function MenusGrid({ onSelectMenuType }) {
  return (
    <div className="grid-wrapper">
      <div className="stages-grid">
        {MENU_TYPES.map((menu) => (
          <div
            key={menu.key}
            className="stage-card"
            onMouseEnter={playHoverSound}
            onClick={() => { playSound('boop'); onSelectMenuType(menu.key) }}
          >
            <div className="stage-icon-container">
              <div className="stage-placeholder" style={{ display: 'flex' }}>
                {menu.short}
              </div>
            </div>

            <div className="stage-info">
              <h3 className="stage-name">{menu.name}</h3>
              <p className="stage-variant-count">{menu.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
