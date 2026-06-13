/**
 * HudMenuTypesGrid - Mod type selector for the in-game HUD.
 *
 * Pause Screen (GmPause overlay) and Percent Font (IfAll damage digits /
 * typeface). More HUD elements (timer, stocks...) can be added here later.
 */
import { playSound, playHoverSound } from '../../utils/sounds'

const HUD_MOD_TYPES = [
  { key: 'pause_screen', name: 'Pause Screen', short: 'PS' },
  { key: 'percent_font', name: 'Percent Font', short: '%' },
  { key: 'ready_go', name: 'Ready / Go / Game', short: 'RG' }
]

export default function HudMenuTypesGrid({ onSelectModType }) {
  return (
    <div className="stages-grid">
      {HUD_MOD_TYPES.map((modType) => (
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
