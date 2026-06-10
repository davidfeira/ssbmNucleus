/**
 * SssMenuTypesGrid - Mod type selector for the Stage Select Screen.
 */
import { playSound, playHoverSound } from '../../utils/sounds'

const SSS_MOD_TYPES = [
  {
    key: 'background',
    name: 'Background',
    short: 'BG',
    description: 'SSS background model and animations'
  }
]

export default function SssMenuTypesGrid({ onSelectModType }) {
  return (
    <div className="stages-grid">
      {SSS_MOD_TYPES.map((modType) => (
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
