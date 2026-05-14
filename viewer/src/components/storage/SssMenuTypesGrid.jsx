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
  },
  {
    key: 'layout',
    name: 'Layout Editor',
    short: 'SSS',
    description: 'Edit stage icon positions and layout'
  }
]

export default function SssMenuTypesGrid({ onSelectModType }) {
  return (
    <div className="stages-grid" style={{ justifyContent: 'center' }}>
      {SSS_MOD_TYPES.map((modType) => (
        <div
          key={modType.key}
          className="stage-card"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('boop'); onSelectModType(modType.key) }}
        >
          <div className="stage-info" style={{ padding: '2rem 1rem' }}>
            <h3 className="stage-name">{modType.name}</h3>
          </div>
        </div>
      ))}
    </div>
  )
}
