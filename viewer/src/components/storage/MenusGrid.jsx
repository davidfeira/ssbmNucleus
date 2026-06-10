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
  },
  {
    key: 'pause',
    name: 'Pause Screen',
    short: 'Pause',
    description: 'In-game pause overlay texture mods'
  }
]

export default function MenusGrid({ onSelectMenuType }) {
  return (
    <div className="stages-grid">
      {MENU_TYPES.map((menu) => (
        <div
          key={menu.key}
          className="stage-card"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); onSelectMenuType(menu.key) }}
        >
          <div className="stage-info menu-type-info">
            <h3 className="stage-name">{menu.name}</h3>
            <p className="menu-type-desc">{menu.description}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
