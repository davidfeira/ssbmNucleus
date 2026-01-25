import { useState, useRef, useEffect, useCallback } from 'react'
import EmbeddedModelViewer from '../EmbeddedModelViewer'
import PoseSkinSelectorModal from './PoseSkinSelectorModal'

/**
 * Pose Manager Modal
 * Allows users to pose characters and save poses for CSP generation
 * Left side: 3D viewer for posing + category buttons
 * Middle: Animation list with human-readable names
 * Right side: Grid of saved poses with thumbnails
 */

// Human-readable animation names
const ANIM_NAMES = {
  // Grounded Attacks
  'Attack11': 'Jab 1', 'Attack12': 'Jab 2', 'Attack13': 'Jab 3',
  'Attack100Start': 'Rapid Jab Start', 'Attack100Loop': 'Rapid Jab Loop', 'Attack100End': 'Rapid Jab End',
  'AttackDash': 'Dash Attack',
  'AttackS3Hi': 'F-Tilt (High)', 'AttackS3HiS': 'F-Tilt (Mid-High)', 'AttackS3S': 'F-Tilt',
  'AttackS3LwS': 'F-Tilt (Mid-Low)', 'AttackS3Lw': 'F-Tilt (Low)',
  'AttackHi3': 'Up Tilt', 'AttackLw3': 'Down Tilt',
  'AttackS4Hi': 'F-Smash (High)', 'AttackS4HiS': 'F-Smash (Mid-High)', 'AttackS4S': 'F-Smash',
  'AttackS4LwS': 'F-Smash (Mid-Low)', 'AttackS4Lw': 'F-Smash (Low)',
  'AttackHi4': 'Up Smash', 'AttackLw4': 'Down Smash',
  // Aerials
  'AttackAirN': 'Neutral Air', 'AttackAirF': 'Forward Air', 'AttackAirB': 'Back Air',
  'AttackAirHi': 'Up Air', 'AttackAirLw': 'Down Air', 'LandingAirN': 'N-Air Landing',
  'LandingAirF': 'F-Air Landing', 'LandingAirB': 'B-Air Landing',
  'LandingAirHi': 'U-Air Landing', 'LandingAirLw': 'D-Air Landing',
  // Specials
  'SpecialN': 'Neutral B', 'SpecialNStart': 'Neutral B Start', 'SpecialNLoop': 'Neutral B Loop',
  'SpecialNEnd': 'Neutral B End', 'SpecialAirN': 'Neutral B (Air)',
  'SpecialS': 'Side B', 'SpecialSStart': 'Side B Start', 'SpecialAirS': 'Side B (Air)',
  'SpecialHi': 'Up B', 'SpecialHiStart': 'Up B Start', 'SpecialAirHi': 'Up B (Air)',
  'SpecialLw': 'Down B', 'SpecialLwStart': 'Down B Start', 'SpecialAirLw': 'Down B (Air)',
  // Grabs & Throws
  'Catch': 'Grab', 'CatchDash': 'Dash Grab', 'CatchWait': 'Grab Hold',
  'CatchAttack': 'Pummel', 'CatchCut': 'Grab Release',
  'ThrowF': 'Forward Throw', 'ThrowB': 'Back Throw', 'ThrowHi': 'Up Throw', 'ThrowLw': 'Down Throw',
  // Movement
  'Wait1': 'Idle 1', 'Wait2': 'Idle 2', 'Wait3': 'Idle 3', 'Wait4': 'Idle 4',
  'Walk': 'Walk', 'WalkSlow': 'Walk (Slow)', 'WalkMiddle': 'Walk (Mid)', 'WalkFast': 'Walk (Fast)',
  'Dash': 'Dash', 'Run': 'Run', 'RunBrake': 'Run Stop',
  'Turn': 'Turn', 'TurnRun': 'Run Turn', 'TurnRunBrake': 'Skid Turn',
  'KneeBend': 'Jumpsquat', 'JumpF': 'Jump (Forward)', 'JumpB': 'Jump (Back)',
  'JumpAerialF': 'Double Jump (F)', 'JumpAerialB': 'Double Jump (B)',
  'Fall': 'Fall', 'FallF': 'Fall (Forward)', 'FallB': 'Fall (Back)',
  'FallAerial': 'Fall (After DJ)', 'FallAerialF': 'Fall (DJ Forward)', 'FallAerialB': 'Fall (DJ Back)',
  'FallSpecial': 'Fall (Special)', 'Landing': 'Landing', 'LandingFallSpecial': 'Landing (Special)',
  'Squat': 'Crouch', 'SquatWait': 'Crouch Idle', 'SquatRv': 'Stand Up',
  'Pass': 'Platform Drop',
  // Defense
  'Guard': 'Shield', 'GuardOn': 'Shield Start', 'GuardOff': 'Shield Drop',
  'GuardReflect': 'Powershield', 'GuardDamage': 'Shield Stun',
  'EscapeN': 'Spot Dodge', 'EscapeF': 'Roll Forward', 'EscapeB': 'Roll Back',
  'EscapeAir': 'Air Dodge',
  // Damage & KO
  'DamageN1': 'Damage (Weak)', 'DamageN2': 'Damage (Mid)', 'DamageN3': 'Damage (Strong)',
  'DamageHi1': 'Damage High (W)', 'DamageHi2': 'Damage High (M)', 'DamageHi3': 'Damage High (S)',
  'DamageLw1': 'Damage Low (W)', 'DamageLw2': 'Damage Low (M)', 'DamageLw3': 'Damage Low (S)',
  'DamageAir1': 'Damage Air (W)', 'DamageAir2': 'Damage Air (M)', 'DamageAir3': 'Damage Air (S)',
  'DamageFlyN': 'Tumble', 'DamageFlyHi': 'Tumble (High)', 'DamageFlyLw': 'Tumble (Low)',
  'DamageFlyTop': 'Tumble (Top)', 'DamageFlyRoll': 'Tumble Roll',
  'DownBoundU': 'Knockdown (Up)', 'DownBoundD': 'Knockdown (Down)',
  'DownWaitU': 'Grounded (Up)', 'DownWaitD': 'Grounded (Down)',
  'DownStandU': 'Getup (Up)', 'DownStandD': 'Getup (Down)',
  'DownAttackU': 'Getup Attack (Up)', 'DownAttackD': 'Getup Attack (Down)',
  'DownForwardU': 'Getup Roll (Fwd)', 'DownBackU': 'Getup Roll (Back)',
  'DownForwardD': 'Getup Roll (Fwd)', 'DownBackD': 'Getup Roll (Back)',
  // Ledge
  'CliffCatch': 'Ledge Grab', 'CliffWait': 'Ledge Hang',
  'CliffClimbSlow': 'Ledge Climb (Slow)', 'CliffClimbQuick': 'Ledge Climb (Fast)',
  'CliffAttackSlow': 'Ledge Attack (Slow)', 'CliffAttackQuick': 'Ledge Attack (Fast)',
  'CliffEscapeSlow': 'Ledge Roll (Slow)', 'CliffEscapeQuick': 'Ledge Roll (Fast)',
  'CliffJumpSlow1': 'Ledge Jump (Slow)', 'CliffJumpQuick1': 'Ledge Jump (Fast)',
  // Misc
  'Appeal': 'Taunt', 'AppealL': 'Taunt (Left)', 'AppealR': 'Taunt (Right)',
  'Entry': 'Entry', 'EntryStart': 'Entry Start', 'EntryEnd': 'Entry End',
  'Win1': 'Victory 1', 'Win2': 'Victory 2', 'Win3': 'Victory 3',
  'Lose': 'Defeat', 'Dead': 'Star KO', 'DeadUp': 'Up KO', 'DeadLeft': 'Side KO',
  'ReboundStop': 'Clang', 'WallDamage': 'Wall Tech Damage',
  'StopCeil': 'Ceiling Tech', 'StopWall': 'Wall Tech', 'WallJump': 'Wall Jump',
  'Ottotto': 'Teeter', 'OttottoWait': 'Teeter Idle',
  'ItemParasolOpen': 'Parasol Open', 'ItemParasolFall': 'Parasol Fall',
  'LightGet': 'Item Pickup (Light)', 'HeavyGet': 'Item Pickup (Heavy)',
  'LightThrowF': 'Throw Item (F)', 'LightThrowB': 'Throw Item (B)',
  'LightThrowHi': 'Throw Item (Up)', 'LightThrowLw': 'Throw Item (Down)',
  'LightThrowDash': 'Throw Item (Dash)', 'LightThrowDrop': 'Drop Item',
  'LightThrowAirF': 'Air Throw (F)', 'LightThrowAirB': 'Air Throw (B)',
  'LightThrowAirHi': 'Air Throw (Up)', 'LightThrowAirLw': 'Air Throw (Down)',
  'SwordSwing1': 'Bat Swing 1', 'SwordSwing3': 'Bat Swing 2', 'SwordSwing4': 'Bat Swing 3',
  'SwordSwingDash': 'Bat Dash', 'BatSwingDash': 'Bat Dash Attack'
}

// Animation categories
const ANIM_CATEGORIES = {
  'Grounded': [
    'Attack11', 'Attack12', 'Attack13', 'Attack100Start', 'Attack100Loop', 'Attack100End',
    'AttackDash', 'AttackS3Hi', 'AttackS3HiS', 'AttackS3S', 'AttackS3LwS', 'AttackS3Lw',
    'AttackHi3', 'AttackLw3', 'AttackS4Hi', 'AttackS4HiS', 'AttackS4S', 'AttackS4LwS', 'AttackS4Lw',
    'AttackHi4', 'AttackLw4'
  ],
  'Aerials': [
    'AttackAirN', 'AttackAirF', 'AttackAirB', 'AttackAirHi', 'AttackAirLw',
    'LandingAirN', 'LandingAirF', 'LandingAirB', 'LandingAirHi', 'LandingAirLw'
  ],
  'Specials': [
    'SpecialN', 'SpecialNStart', 'SpecialNLoop', 'SpecialNEnd', 'SpecialAirN',
    'SpecialS', 'SpecialSStart', 'SpecialAirS',
    'SpecialHi', 'SpecialHiStart', 'SpecialAirHi',
    'SpecialLw', 'SpecialLwStart', 'SpecialAirLw'
  ],
  'Grabs': [
    'Catch', 'CatchDash', 'CatchWait', 'CatchAttack', 'CatchCut',
    'ThrowF', 'ThrowB', 'ThrowHi', 'ThrowLw'
  ],
  'Movement': [
    'Wait1', 'Wait2', 'Wait3', 'Wait4', 'Walk', 'WalkSlow', 'WalkMiddle', 'WalkFast',
    'Dash', 'Run', 'RunBrake', 'Turn', 'TurnRun', 'TurnRunBrake',
    'KneeBend', 'JumpF', 'JumpB', 'JumpAerialF', 'JumpAerialB',
    'Fall', 'FallF', 'FallB', 'FallAerial', 'FallAerialF', 'FallAerialB',
    'FallSpecial', 'Landing', 'LandingFallSpecial', 'Squat', 'SquatWait', 'SquatRv', 'Pass'
  ],
  'Defense': [
    'Guard', 'GuardOn', 'GuardOff', 'GuardReflect', 'GuardDamage',
    'EscapeN', 'EscapeF', 'EscapeB', 'EscapeAir'
  ],
  'Damage': [
    'DamageN1', 'DamageN2', 'DamageN3', 'DamageHi1', 'DamageHi2', 'DamageHi3',
    'DamageLw1', 'DamageLw2', 'DamageLw3', 'DamageAir1', 'DamageAir2', 'DamageAir3',
    'DamageFlyN', 'DamageFlyHi', 'DamageFlyLw', 'DamageFlyTop', 'DamageFlyRoll',
    'DownBoundU', 'DownBoundD', 'DownWaitU', 'DownWaitD', 'DownStandU', 'DownStandD',
    'DownAttackU', 'DownAttackD', 'DownForwardU', 'DownBackU', 'DownForwardD', 'DownBackD'
  ],
  'Ledge': [
    'CliffCatch', 'CliffWait', 'CliffClimbSlow', 'CliffClimbQuick',
    'CliffAttackSlow', 'CliffAttackQuick', 'CliffEscapeSlow', 'CliffEscapeQuick',
    'CliffJumpSlow1', 'CliffJumpQuick1'
  ],
  'Misc': [
    'Appeal', 'AppealL', 'AppealR', 'Entry', 'EntryStart', 'EntryEnd',
    'Win1', 'Win2', 'Win3', 'Lose', 'Dead', 'DeadUp', 'DeadLeft',
    'ReboundStop', 'WallDamage', 'StopCeil', 'StopWall', 'WallJump',
    'Ottotto', 'OttottoWait', 'ItemParasolOpen', 'ItemParasolFall',
    'LightGet', 'HeavyGet', 'LightThrowF', 'LightThrowB', 'LightThrowHi', 'LightThrowLw',
    'LightThrowDash', 'LightThrowDrop', 'LightThrowAirF', 'LightThrowAirB',
    'LightThrowAirHi', 'LightThrowAirLw', 'SwordSwing1', 'SwordSwing3', 'SwordSwing4',
    'SwordSwingDash', 'BatSwingDash'
  ]
}

// Extract base animation name from symbol (e.g., "PlFx_Share_ACTION_Wait1_figatree" -> "Wait1")
const extractAnimName = (symbol) => {
  const match = symbol.match(/ACTION_(\w+)_figatree/)
  return match ? match[1] : symbol
}

// Get human-readable display name for animation
const getAnimDisplayName = (symbol) => {
  const baseName = extractAnimName(symbol)
  return ANIM_NAMES[baseName] || baseName
}

// Get category for an animation
const getAnimCategory = (symbol) => {
  const baseName = extractAnimName(symbol)
  for (const [category, anims] of Object.entries(ANIM_CATEGORIES)) {
    if (anims.includes(baseName)) return category
  }
  return 'Other'
}

// Character to costume code prefix mapping
const CHAR_PREFIXES = {
  "C. Falcon": "PlCa", "Falco": "PlFc", "Fox": "PlFx",
  "Marth": "PlMs", "Roy": "PlFe", "Bowser": "PlKp",
  "DK": "PlDk", "Ganondorf": "PlGn", "Jigglypuff": "PlPr",
  "Kirby": "PlKb", "Link": "PlLk", "Luigi": "PlLg",
  "Mario": "PlMr", "Mewtwo": "PlMt", "Ness": "PlNs",
  "Peach": "PlPe", "Pichu": "PlPc", "Pikachu": "PlPk",
  "Ice Climbers": "PlPp", "Samus": "PlSs", "Sheik": "PlSk",
  "Yoshi": "PlYs", "Young Link": "PlCl", "Zelda": "PlZd",
  "Dr. Mario": "PlDr", "G&W": "PlGw"
}

// Get default costume code for a character (e.g., "PlFxNr" for Fox)
const getDefaultCostumeCode = (character) => {
  const prefix = CHAR_PREFIXES[character]
  return prefix ? `${prefix}Nr` : null
}

const CloseIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="6" x2="6" y2="18"/>
    <line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
)

const SaveIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
    <polyline points="17 21 17 13 7 13 7 21"/>
    <polyline points="7 3 7 8 15 8"/>
  </svg>
)

const TrashIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>
)

// Pose Card Component
function PoseCard({ pose, character, onDelete, onClick, API_URL }) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async (e) => {
    e.stopPropagation()
    if (!confirm(`Delete pose "${pose.name}"?`)) return

    setDeleting(true)
    try {
      const response = await fetch(`${API_URL}/storage/poses/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character, poseName: pose.name })
      })
      const data = await response.json()
      if (data.success) {
        onDelete(pose.name)
      }
    } catch (err) {
      console.error('[PoseCard] Delete error:', err)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="pm-pose-card" onClick={onClick} style={{ cursor: 'pointer' }}>
      <div className="pm-pose-image">
        {pose.hasThumbnail ? (
          <img
            src={`${API_URL.replace('/api/mex', '')}${pose.thumbnailUrl}`}
            alt={pose.name}
            onError={(e) => { e.target.style.display = 'none' }}
          />
        ) : (
          <div className="pm-pose-placeholder">
            {pose.name.charAt(0).toUpperCase()}
          </div>
        )}
        <button
          className="pm-pose-delete"
          onClick={handleDelete}
          disabled={deleting}
          title="Delete pose"
        >
          <TrashIcon />
        </button>
      </div>
      <div className="pm-pose-name">{pose.name}</div>
    </div>
  )
}

export default function PoseManagerModal({
  show,
  character,
  onClose,
  onRefresh,
  API_URL
}) {
  const [poseName, setPoseName] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [poses, setPoses] = useState([])
  const [loadingPoses, setLoadingPoses] = useState(true)
  const [selectedPose, setSelectedPose] = useState(null) // For skin selector modal
  const [animList, setAnimList] = useState([])
  const [selectedAnim, setSelectedAnim] = useState('')
  const [animFilter, setAnimFilter] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const viewerRef = useRef(null)

  // Poll viewer for animation list
  useEffect(() => {
    if (!show) return
    const interval = setInterval(() => {
      if (viewerRef.current?.animList?.length > 0) {
        setAnimList(viewerRef.current.animList)
        if (viewerRef.current.selectedAnim) {
          setSelectedAnim(viewerRef.current.selectedAnim)
        }
      }
    }, 500)
    return () => clearInterval(interval)
  }, [show])

  const handleLoadAnim = (symbol) => {
    if (viewerRef.current?.loadAnimation) {
      viewerRef.current.loadAnimation(symbol)
      setSelectedAnim(symbol)
    }
  }

  // Fetch saved poses
  const fetchPoses = useCallback(async () => {
    if (!character) return
    try {
      const response = await fetch(`${API_URL}/storage/poses/list/${character}`)
      const data = await response.json()
      if (data.success) {
        setPoses(data.poses)
      }
    } catch (err) {
      console.error('[PoseManager] Fetch poses error:', err)
    } finally {
      setLoadingPoses(false)
    }
  }, [character, API_URL])

  useEffect(() => {
    if (show) {
      fetchPoses()
    }
  }, [show, fetchPoses])

  if (!show) return null

  const handleSavePose = async () => {
    if (!poseName.trim()) {
      setSaveError('Please enter a pose name')
      return
    }

    if (!viewerRef.current) {
      setSaveError('Viewer not ready')
      return
    }

    setSaving(true)
    setSaveError(null)
    setSaveSuccess(false)

    try {
      // Export scene from viewer
      const sceneData = await viewerRef.current.exportScene()
      if (!sceneData) {
        throw new Error('Failed to export scene data')
      }

      // Save pose via API
      const response = await fetch(`${API_URL}/storage/poses/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character,
          poseName: poseName.trim(),
          sceneData
        })
      })

      const data = await response.json()
      if (!data.success) {
        throw new Error(data.error || 'Failed to save pose')
      }

      setSaveSuccess(true)
      setPoseName('')

      // Refresh poses list to show new thumbnail
      await fetchPoses()

      // Clear success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err) {
      console.error('[PoseManager] Save error:', err)
      setSaveError(err.message || 'Failed to save pose')
    } finally {
      setSaving(false)
    }
  }

  const handleDeletePose = (poseName) => {
    setPoses(poses.filter(p => p.name !== poseName))
  }

  return (
    <div className="pm-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="pm-modal">
        {/* Header */}
        <div className="pm-header">
          <div className="pm-title">
            <span className="pm-title-label">Pose Manager</span>
            <span className="pm-title-char">{character}</span>
          </div>
          <button className="pm-close-btn" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        {/* Body with viewer and poses grid */}
        <div className="pm-body">
          {/* Left: Viewer + Category Buttons */}
          {!selectedPose && (
            <div className="pm-left-section">
              <div className="pm-viewer-section">
                <EmbeddedModelViewer
                  ref={viewerRef}
                  character={character}
                  costumeCode={getDefaultCostumeCode(character)}
                  onClose={onClose}
                  cspMode={true}
                  showGrid={false}
                  showBackground={false}
                />
              </div>

              {/* Category buttons below viewer */}
              <div className="pm-category-bar">
                <button
                  className={`pm-cat-btn ${selectedCategory === 'All' ? 'active' : ''}`}
                  onClick={() => setSelectedCategory('All')}
                >
                  All
                </button>
                {Object.keys(ANIM_CATEGORIES).map(cat => (
                  <button
                    key={cat}
                    className={`pm-cat-btn ${selectedCategory === cat ? 'active' : ''}`}
                    onClick={() => setSelectedCategory(cat)}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Middle: Animation List (bigger) */}
          {!selectedPose && animList.length > 0 && (
            <div className="pm-anim-section">
              <div className="pm-anim-header">
                <span>Animations</span>
                <span className="pm-anim-count">
                  {animList.filter(a => {
                    const matchesCategory = selectedCategory === 'All' || getAnimCategory(a) === selectedCategory
                    const matchesFilter = a.toLowerCase().includes(animFilter.toLowerCase()) ||
                                          getAnimDisplayName(a).toLowerCase().includes(animFilter.toLowerCase())
                    return matchesCategory && matchesFilter
                  }).length}
                </span>
              </div>
              <input
                type="text"
                className="pm-anim-filter"
                placeholder="Search animations..."
                value={animFilter}
                onChange={(e) => setAnimFilter(e.target.value)}
              />
              <div className="pm-anim-list">
                {animList
                  .filter(a => {
                    const matchesCategory = selectedCategory === 'All' || getAnimCategory(a) === selectedCategory
                    const matchesFilter = a.toLowerCase().includes(animFilter.toLowerCase()) ||
                                          getAnimDisplayName(a).toLowerCase().includes(animFilter.toLowerCase())
                    return matchesCategory && matchesFilter
                  })
                  .map(anim => (
                    <button
                      key={anim}
                      className={`pm-anim-item ${selectedAnim === anim ? 'active' : ''}`}
                      onClick={() => handleLoadAnim(anim)}
                      title={anim}
                    >
                      {getAnimDisplayName(anim)}
                    </button>
                  ))}
              </div>
            </div>
          )}

          {/* Right: Saved Poses (smaller) */}
          <div className="pm-poses-section">
            <div className="pm-poses-header">
              <span>Saved Poses</span>
              <span className="pm-poses-count">{poses.length}</span>
            </div>
            <div className="pm-poses-grid">
              {loadingPoses ? (
                <div className="pm-poses-loading">Loading poses...</div>
              ) : poses.length === 0 ? (
                <div className="pm-poses-empty">
                  No saved poses yet.<br/>
                  Create a pose and save it!
                </div>
              ) : (
                poses.map(pose => (
                  <PoseCard
                    key={pose.name}
                    pose={pose}
                    character={character}
                    onDelete={handleDeletePose}
                    onClick={() => setSelectedPose(pose)}
                    API_URL={API_URL}
                  />
                ))
              )}
            </div>
          </div>
        </div>

        {/* Save controls */}
        <div className="pm-save-controls">
          <input
            type="text"
            className="pm-pose-name-input"
            placeholder="Enter pose name..."
            value={poseName}
            onChange={(e) => setPoseName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSavePose()}
            disabled={saving}
          />
          <button
            className="pm-save-btn"
            onClick={handleSavePose}
            disabled={saving || !poseName.trim()}
          >
            <SaveIcon />
            <span>{saving ? 'Saving...' : 'Save Pose'}</span>
          </button>
        </div>

        {/* Status messages */}
        {saveError && (
          <div className="pm-message pm-error">
            {saveError}
          </div>
        )}
        {saveSuccess && (
          <div className="pm-message pm-success">
            Pose saved successfully!
          </div>
        )}
      </div>

      {/* Skin Selector Modal for batch CSP generation */}
      <PoseSkinSelectorModal
        show={selectedPose !== null}
        character={character}
        poseName={selectedPose?.name}
        poseThumbnail={selectedPose?.hasThumbnail ? `${API_URL.replace('/api/mex', '')}${selectedPose.thumbnailUrl}` : null}
        onClose={() => setSelectedPose(null)}
        onRefresh={onRefresh}
        API_URL={API_URL}
      />

      <style>{`
        .pm-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .pm-modal {
          background: #1a1a2e;
          border-radius: 12px;
          width: 65vw;
          height: 80vh;
          max-width: 1000px;
          max-height: 900px;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        @media (min-width: 1440px) {
          .pm-modal {
            max-width: 1100px;
            max-height: 1000px;
          }
        }

        @media (min-width: 1920px) {
          .pm-modal {
            max-width: 1250px;
            max-height: 1100px;
          }
        }

        @media (min-width: 2560px) {
          .pm-modal {
            max-width: 1500px;
            max-height: 1300px;
          }
        }

        .pm-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          background: #16162a;
          border-bottom: 1px solid #2a2a4a;
        }

        .pm-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .pm-title-label {
          font-size: 18px;
          font-weight: 600;
          color: #fff;
        }

        .pm-title-char {
          font-size: 14px;
          color: #888;
          padding: 4px 10px;
          background: #2a2a4a;
          border-radius: 4px;
        }

        .pm-close-btn {
          background: transparent;
          border: none;
          color: #888;
          cursor: pointer;
          padding: 8px;
          border-radius: 6px;
          transition: all 0.15s ease;
        }

        .pm-close-btn:hover {
          background: #2a2a4a;
          color: #fff;
        }

        .pm-body {
          flex: 1;
          display: flex;
          overflow: hidden;
        }

        /* Left: Viewer + Category Section */
        .pm-left-section {
          display: flex;
          flex-direction: column;
          flex: 1;
          border-right: 1px solid #2a2a4a;
        }

        .pm-viewer-section {
          flex: 1;
          position: relative;
          overflow: hidden;
        }

        /* Category bar below viewer */
        .pm-category-bar {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          padding: 10px 12px;
          background: #16162a;
          border-top: 1px solid #2a2a4a;
        }

        .pm-cat-btn {
          padding: 5px 10px;
          background: #2a2a4a;
          border: none;
          border-radius: 4px;
          color: #888;
          font-size: 11px;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .pm-cat-btn:hover {
          background: #3a3a5a;
          color: #ccc;
        }

        .pm-cat-btn.active {
          background: #4a9eff;
          color: #fff;
        }

        .pm-viewer-section .mv-overlay {
          position: absolute !important;
          inset: 0 !important;
          width: 100% !important;
          height: 100% !important;
          background: transparent !important;
          backdrop-filter: none !important;
          z-index: 1 !important;
        }

        .pm-viewer-section .mv-container {
          width: 100% !important;
          height: 100% !important;
          max-width: none !important;
          max-height: none !important;
          border-radius: 0 !important;
          border: none !important;
          box-shadow: none !important;
          background:
            radial-gradient(ellipse at 50% 30%, rgba(125, 211, 232, 0.03) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(125, 211, 232, 0.02) 0%, transparent 40%),
            linear-gradient(180deg, #0d1929 0%, #0a1420 100%) !important;
        }

        .pm-viewer-section .mv-header {
          display: none !important;
        }

        .pm-viewer-section .mv-body {
          flex: 1 !important;
          min-height: 0 !important;
        }

        .pm-viewer-section .mv-viewport {
          flex: 1 !important;
          margin: 0 !important;
          border: none !important;
          border-radius: 0 !important;
          min-height: 0 !important;
          background: transparent !important;
        }

        .pm-viewer-section .mv-sidebar {
          display: none;
        }

        .pm-viewer-section .mv-controls {
          background: rgba(0, 0, 0, 0.5);
          border-top: 1px solid #2a2a4a;
        }

        /* Right: Poses Section */
        .pm-poses-section {
          width: 260px;
          min-width: 240px;
          display: flex;
          flex-direction: column;
          background: #16162a;
        }

        .pm-poses-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          border-bottom: 1px solid #2a2a4a;
          font-size: 14px;
          font-weight: 500;
          color: #fff;
        }

        .pm-poses-count {
          background: #2a2a4a;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 12px;
          color: #888;
        }

        .pm-poses-grid {
          flex: 1;
          overflow-y: auto;
          padding: 10px;
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 10px;
          align-content: start;
        }

        .pm-poses-loading,
        .pm-poses-empty {
          grid-column: 1 / -1;
          text-align: center;
          color: #666;
          font-size: 13px;
          padding: 40px 20px;
          line-height: 1.6;
        }

        /* Pose Card */
        .pm-pose-card {
          background: #1a1a2e;
          border: 1px solid #2a2a4a;
          border-radius: 8px;
          overflow: hidden;
          transition: all 0.15s ease;
        }

        .pm-pose-card:hover {
          border-color: #4a9eff;
          transform: translateY(-2px);
        }

        .pm-pose-image {
          position: relative;
          aspect-ratio: 3 / 4;
          background: #0d1929;
          overflow: hidden;
        }

        .pm-pose-image img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .pm-pose-placeholder {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 32px;
          font-weight: 600;
          color: #2a2a4a;
          background: linear-gradient(135deg, #1a1a2e 0%, #0d1929 100%);
        }

        .pm-pose-delete {
          position: absolute;
          top: 6px;
          right: 6px;
          background: rgba(220, 53, 69, 0.9);
          border: none;
          border-radius: 4px;
          padding: 6px;
          color: #fff;
          cursor: pointer;
          opacity: 0;
          transition: opacity 0.15s ease;
        }

        .pm-pose-card:hover .pm-pose-delete {
          opacity: 1;
        }

        .pm-pose-delete:hover {
          background: #dc3545;
        }

        .pm-pose-name {
          padding: 8px;
          font-size: 12px;
          color: #ccc;
          text-align: center;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .pm-save-controls {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px 20px;
          background: #16162a;
          border-top: 1px solid #2a2a4a;
        }

        .pm-pose-name-input {
          flex: 1;
          padding: 12px 16px;
          background: #1a1a2e;
          border: 1px solid #2a2a4a;
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          outline: none;
          transition: border-color 0.15s ease;
        }

        .pm-pose-name-input:focus {
          border-color: #4a9eff;
        }

        .pm-pose-name-input::placeholder {
          color: #666;
        }

        .pm-pose-name-input:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .pm-save-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: linear-gradient(135deg, #4a9eff, #3d7ede);
          border: none;
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .pm-save-btn:hover:not(:disabled) {
          background: linear-gradient(135deg, #5aadff, #4d8eee);
          transform: translateY(-1px);
        }

        .pm-save-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .pm-message {
          padding: 12px 20px;
          font-size: 14px;
          text-align: center;
        }

        .pm-error {
          background: rgba(220, 53, 69, 0.2);
          color: #ff6b6b;
          border-top: 1px solid rgba(220, 53, 69, 0.3);
        }

        .pm-success {
          background: rgba(40, 167, 69, 0.2);
          color: #51cf66;
          border-top: 1px solid rgba(40, 167, 69, 0.3);
        }
      `}</style>
    </div>
  )
}
