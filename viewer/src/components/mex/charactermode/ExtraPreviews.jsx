/**
 * Extra preview components for CharacterMode extras mode.
 * Pure presentational components - no state, no API calls.
 */
import { rgbyToHex } from '../../../utils/rgbyColor'

// Laser beam preview component for extras
export const LaserBeamPreview = ({ modifications, compact = false }) => {
  const getColor = (layerId) => {
    const mod = modifications?.[layerId]
    if (!mod?.color) return null
    // Center layer is RGB format, others are RGBY
    if (layerId === 'center') {
      return `#${mod.color}`
    }
    return rgbyToHex(mod.color)
  }

  const wide = getColor('wide') || '#ff0000'
  const thin = getColor('thin') || '#ff0000'
  const outline = getColor('outline') || '#ff0000'
  const center = getColor('center') || '#ffffff'
  const height = compact ? 40 : 50

  return (
    <div style={{
      position: 'relative',
      height: `${height}px`,
      width: '100%',
      background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      overflow: 'hidden'
    }}>
      <div style={{
        position: 'absolute', left: '8%', right: '8%',
        height: compact ? '24px' : '30px', borderRadius: '100px',
        background: `linear-gradient(90deg, transparent 0%, ${wide} 5%, ${wide} 95%, transparent 100%)`,
        boxShadow: `0 0 15px ${wide}50, 0 0 30px ${wide}30`, opacity: 0.5
      }} />
      <div style={{
        position: 'absolute', left: '8%', right: '8%',
        height: compact ? '14px' : '18px', borderRadius: '100px',
        background: `linear-gradient(90deg, transparent 0%, ${thin} 3%, ${thin} 97%, transparent 100%)`,
        boxShadow: `0 0 8px ${thin}70`, opacity: 0.7
      }} />
      <div style={{
        position: 'absolute', left: '8%', right: '8%',
        height: compact ? '8px' : '10px', borderRadius: '100px',
        background: `linear-gradient(90deg, transparent 0%, ${outline} 2%, ${outline} 98%, transparent 100%)`,
        boxShadow: `0 0 5px ${outline}90`, opacity: 0.9
      }} />
      <div style={{
        position: 'absolute', left: '8%', right: '8%',
        height: '3px', borderRadius: '100px',
        background: `linear-gradient(90deg, transparent 0%, ${center} 2%, ${center} 98%, transparent 100%)`,
        boxShadow: `0 0 3px ${center}`
      }} />
    </div>
  )
}

// Side-B preview component for extras
export const SideBPreview = ({ modifications, compact = false }) => {
  const getColor = (layerId) => {
    const mod = modifications?.[layerId]
    if (!mod?.color) return null
    // RGBA format: first 6 chars are RGB
    const hex = mod.color.substring(0, 6)
    return `#${hex}`
  }

  const primary = getColor('primary') || '#0099FF'
  const secondary = getColor('secondary') || '#CCE6FF'
  const tertiary = getColor('tertiary') || '#FFFFFF'
  const height = compact ? 40 : 50

  return (
    <div style={{
      position: 'relative',
      height: `${height}px`,
      width: '100%',
      background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      overflow: 'hidden',
      padding: '0 8px'
    }}>
      {[0.15, 0.3, 0.5, 0.7].map((opacity, i) => (
        <div key={i} style={{
          position: 'absolute',
          left: `${10 + i * 18}%`,
          width: compact ? '16px' : '20px',
          height: compact ? '24px' : '30px',
          borderRadius: '4px',
          background: `linear-gradient(135deg, ${primary} 0%, ${secondary} 50%, ${tertiary} 100%)`,
          opacity: opacity,
          boxShadow: `0 0 ${8 + i * 4}px ${primary}40`
        }} />
      ))}
      <div style={{
        position: 'absolute',
        right: '12%',
        width: compact ? '20px' : '24px',
        height: compact ? '28px' : '34px',
        borderRadius: '4px',
        background: `linear-gradient(135deg, ${primary} 0%, ${secondary} 50%, ${tertiary} 100%)`,
        boxShadow: `0 0 12px ${primary}60, 0 0 20px ${secondary}40`
      }} />
    </div>
  )
}

// Up-B preview component for Firefox/Firebird flame (all colors)
export const UpBPreview = ({ modifications, compact = false }) => {
  const tipColor = modifications?.tip?.color ? rgbyToHex(modifications.tip.color) : '#FF6600'
  const bodyColor = modifications?.body?.color ? `#${modifications.body.color}` : '#FFFFFF'
  const trailColor = modifications?.trail?.color ? `#${modifications.trail.color}` : '#FFFFFF'
  const ringsColor = modifications?.rings?.color ? `#${modifications.rings.color}` : '#FFFF00'

  const height = compact ? 40 : 50

  return (
    <div style={{
      position: 'relative',
      height: `${height}px`,
      width: '100%',
      background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden'
    }}>
      {/* Fire ring */}
      <div style={{
        position: 'absolute',
        width: compact ? '50px' : '60px',
        height: compact ? '16px' : '20px',
        bottom: compact ? '8px' : '10px',
        borderRadius: '50%',
        border: `2px solid ${ringsColor}`,
        boxShadow: `0 0 6px ${ringsColor}`,
        opacity: 0.6
      }} />
      {/* Body glow */}
      <div style={{
        position: 'absolute',
        width: compact ? '24px' : '30px',
        height: compact ? '40px' : '50px',
        bottom: compact ? '5px' : '5px',
        background: `radial-gradient(ellipse at center, ${bodyColor}30 0%, transparent 70%)`,
        filter: `drop-shadow(0 0 8px ${bodyColor}40)`
      }} />
      {/* Trail particles */}
      {[0.3, 0.5].map((opacity, i) => (
        <div key={i} style={{
          position: 'absolute',
          width: '6px',
          height: '6px',
          bottom: `${compact ? 20 : 25 + i * 10}px`,
          left: `${45 + (i % 2 ? 5 : -5)}%`,
          borderRadius: '50%',
          background: trailColor,
          opacity: opacity,
          boxShadow: `0 0 3px ${trailColor}`
        }} />
      ))}
      {/* Main flame */}
      <div style={{
        position: 'absolute',
        width: compact ? '18px' : '22px',
        height: compact ? '28px' : '34px',
        bottom: compact ? '2px' : '0',
        borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
        background: `linear-gradient(to top, ${tipColor} 0%, ${tipColor}CC 40%, ${tipColor}66 70%, transparent 100%)`,
        filter: `drop-shadow(0 0 5px ${tipColor})`
      }} />
      {/* Inner core */}
      <div style={{
        position: 'absolute',
        width: compact ? '8px' : '10px',
        height: compact ? '14px' : '18px',
        bottom: compact ? '4px' : '3px',
        borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
        background: `linear-gradient(to top, #FFFFFF 0%, ${tipColor} 60%, transparent 100%)`
      }} />
    </div>
  )
}

// Laser Ring preview component for Fox/Falco laser hit ring effect
export const LaserRingPreview = ({ modifications, compact = false }) => {
  const color1 = modifications?.color1?.color ? `#${modifications.color1.color}` : '#FF004C'
  const color2 = modifications?.color2?.color ? `#${modifications.color2.color}` : '#B20000'
  const height = compact ? 40 : 50

  return (
    <div style={{
      position: 'relative',
      height: `${height}px`,
      width: '100%',
      background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden'
    }}>
      {/* Outer glow - secondary color */}
      <div style={{
        position: 'absolute',
        width: compact ? '50px' : '60px',
        height: compact ? '50px' : '60px',
        borderRadius: '50%',
        background: `radial-gradient(ellipse at center, ${color2}40 0%, transparent 70%)`,
        filter: `drop-shadow(0 0 10px ${color2}50)`
      }} />
      {/* Main ring - primary color */}
      <div style={{
        position: 'absolute',
        width: compact ? '38px' : '46px',
        height: compact ? '38px' : '46px',
        borderRadius: '50%',
        border: `3px solid ${color1}`,
        boxShadow: `0 0 10px ${color1}, inset 0 0 10px ${color1}40`
      }} />
      {/* Inner ring - primary color */}
      <div style={{
        position: 'absolute',
        width: compact ? '20px' : '24px',
        height: compact ? '20px' : '24px',
        borderRadius: '50%',
        border: `2px solid ${color1}`,
        opacity: 0.6
      }} />
      {/* Center dot - primary color */}
      <div style={{
        position: 'absolute',
        width: compact ? '6px' : '8px',
        height: compact ? '6px' : '8px',
        borderRadius: '50%',
        background: color1,
        boxShadow: `0 0 5px ${color1}`
      }} />
    </div>
  )
}

// Shine preview component for reflector shield (two-color gradient)
export const ShinePreview = ({ modifications, compact = false }) => {
  // Get colors from modifications (new two-color gradient format)
  const primaryColor = modifications?.primary?.color ? rgbyToHex(modifications.primary.color) : '#0066FF'
  const secondaryColor = modifications?.secondary?.color ? rgbyToHex(modifications.secondary.color) : '#8888AA'

  const size = compact ? 36 : 50

  return (
    <div style={{
      position: 'relative',
      height: `${size}px`,
      width: '100%',
      background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden'
    }}>
      {/* Outer glow using primary */}
      <div style={{
        position: 'absolute',
        width: compact ? '45px' : '60px',
        height: compact ? '45px' : '60px',
        background: `radial-gradient(ellipse at center, ${primaryColor}50 0%, transparent 70%)`,
        filter: `drop-shadow(0 0 10px ${primaryColor}60)`
      }} />
      {/* Fill glow using secondary */}
      <div style={{
        position: 'absolute',
        width: compact ? '35px' : '45px',
        height: compact ? '35px' : '45px',
        background: `radial-gradient(ellipse at center, ${secondaryColor}80 0%, ${secondaryColor}40 40%, transparent 70%)`
      }} />
      {/* Hexagon with gradient from secondary (fill) to primary (edge) */}
      <div style={{
        position: 'absolute',
        width: compact ? '26px' : '34px',
        height: compact ? '26px' : '34px',
        background: `radial-gradient(circle at center, ${secondaryColor} 30%, ${primaryColor} 100%)`,
        clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
        opacity: 0.9,
        boxShadow: `0 0 8px ${primaryColor}`
      }} />
      {/* Edge highlight */}
      <div style={{
        position: 'absolute',
        width: compact ? '28px' : '36px',
        height: compact ? '28px' : '36px',
        border: `2px solid ${primaryColor}`,
        clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
        opacity: 0.7
      }} />
    </div>
  )
}

// Sword preview component for sword trail
export const SwordPreview = ({ modifications, compact = false }) => {
  const mainColor = modifications?.main?.color ? `#${modifications.main.color}` : '#FF0000'
  const secondaryColor = modifications?.secondary?.color ? `#${modifications.secondary.color}` : '#FFFF00'
  const tertiaryColor = modifications?.tertiary?.color ? `#${modifications.tertiary.color}` : '#FFFFFF'

  const height = compact ? 40 : 50

  return (
    <div style={{
      position: 'relative',
      height: `${height}px`,
      width: '100%',
      background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden'
    }}>
      <svg width={compact ? 80 : 100} height={compact ? 35 : 45} viewBox="0 0 100 45" style={{ overflow: 'visible' }}>
        {/* Outer edge (tertiary) */}
        <path
          d="M 5 40 Q 50 0 95 40"
          fill="none"
          stroke={tertiaryColor}
          strokeWidth={compact ? 12 : 14}
          strokeLinecap="round"
          opacity="0.5"
        />
        {/* Middle (secondary) */}
        <path
          d="M 5 40 Q 50 0 95 40"
          fill="none"
          stroke={secondaryColor}
          strokeWidth={compact ? 7 : 9}
          strokeLinecap="round"
          opacity="0.7"
        />
        {/* Inner core (main) */}
        <path
          d="M 5 40 Q 50 0 95 40"
          fill="none"
          stroke={mainColor}
          strokeWidth={compact ? 3 : 4}
          strokeLinecap="round"
        />
      </svg>
    </div>
  )
}

// Dual color preview for 2-color effects (punch, thunder, fireball, shadow ball)
export const DualColorPreview = ({ extraType, modifications, compact = false }) => {
  // Get colors - handle both color1/color2 and tip_color1/tip_color2 formats
  const color1 = modifications?.color1?.color || modifications?.tip_color1?.color || 'FFFFFF'
  const color2 = modifications?.color2?.color || modifications?.tip_color2?.color || '0000FF'
  const color1Hex = `#${color1}`
  const color2Hex = `#${color2}`

  const height = compact ? 40 : 50

  // Punch effect - explosion/flame burst
  if (extraType?.id === 'falcon_punch' || extraType?.id === 'warlock_punch') {
    return (
      <div style={{
        position: 'relative',
        height: `${height}px`,
        width: '100%',
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        <svg width={compact ? 80 : 100} height={compact ? 36 : 45} viewBox="0 0 100 45">
          <ellipse cx="50" cy="22" rx="40" ry="18" fill={color2Hex} opacity="0.3" />
          <ellipse cx="50" cy="22" rx="28" ry="12" fill={color1Hex} opacity="0.6" />
          <ellipse cx="50" cy="22" rx="15" ry="6" fill={color1Hex} />
        </svg>
      </div>
    )
  }

  // Thunder effect - lightning bolt
  if (extraType?.id === 'thunder' || extraType?.id === 'pk_thunder') {
    return (
      <div style={{
        position: 'relative',
        height: `${height}px`,
        width: '100%',
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        <svg width={compact ? 60 : 80} height={compact ? 36 : 45} viewBox="0 0 80 45">
          <path d="M42 3 L28 18 L38 18 L24 42 L56 22 L44 22 L58 3 Z"
            fill={color2Hex} opacity="0.4" transform="scale(1.1) translate(-4, -2)" />
          <path d="M42 3 L28 18 L38 18 L24 42 L56 22 L44 22 L58 3 Z"
            fill={color1Hex} />
        </svg>
      </div>
    )
  }

  // Fireball effect
  if (extraType?.id === 'fireball') {
    return (
      <div style={{
        position: 'relative',
        height: `${height}px`,
        width: '100%',
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        <svg width={compact ? 60 : 80} height={compact ? 36 : 45} viewBox="0 0 80 45">
          <circle cx="40" cy="22" r="18" fill={color2Hex} opacity="0.4" />
          <circle cx="40" cy="22" r="12" fill={color1Hex} opacity="0.7" />
          <circle cx="40" cy="22" r="6" fill={color1Hex} />
        </svg>
      </div>
    )
  }

  // Shadow Ball effect
  if (extraType?.id === 'shadow_ball') {
    return (
      <div style={{
        position: 'relative',
        height: `${height}px`,
        width: '100%',
        background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        <svg width={compact ? 60 : 80} height={compact ? 36 : 45} viewBox="0 0 80 45">
          <circle cx="40" cy="22" r="18" fill={color2Hex} opacity="0.3" />
          <circle cx="40" cy="22" r="13" fill={color1Hex} opacity="0.5" />
          <circle cx="40" cy="22" r="7" fill={color1Hex} />
        </svg>
      </div>
    )
  }

  // Default dual-color
  return (
    <div style={{
      position: 'relative',
      height: `${height}px`,
      width: '100%',
      background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden'
    }}>
      <svg width={compact ? 80 : 100} height={compact ? 36 : 45} viewBox="0 0 100 45">
        <circle cx="35" cy="22" r="14" fill={color1Hex} />
        <circle cx="65" cy="22" r="14" fill={color2Hex} />
      </svg>
    </div>
  )
}

// Model preview for 3D model extras (gun, etc.)
export const ModelPreview = ({ mod, compact = false }) => {
  const height = compact ? 40 : 50

  return (
    <div style={{
      position: 'relative',
      height: `${height}px`,
      width: '100%',
      background: 'linear-gradient(180deg, #0a0a12 0%, #0d0d18 100%)',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden'
    }}>
      {/* 3D cube icon */}
      <svg
        width={compact ? 24 : 32}
        height={compact ? 24 : 32}
        viewBox="0 0 24 24"
        fill="none"
        stroke="#4a9eff"
        strokeWidth="1.5"
      >
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
      {mod?.name && (
        <span style={{
          position: 'absolute',
          bottom: '4px',
          fontSize: '9px',
          color: '#666'
        }}>
          3D Model
        </span>
      )}
    </div>
  )
}

// Generic extra preview that switches based on type
export const ExtraPreview = ({ extraType, modifications, mod, compact = false }) => {
  const typeId = extraType?.id

  // Model types (gun, etc.)
  if (extraType?.type === 'model') {
    return <ModelPreview mod={mod} compact={compact} />
  }
  // Fox/Falco extras
  if (typeId === 'laser') {
    return <LaserBeamPreview modifications={modifications} compact={compact} />
  }
  if (typeId === 'sideb') {
    return <SideBPreview modifications={modifications} compact={compact} />
  }
  if (typeId === 'upb') {
    return <UpBPreview modifications={modifications} compact={compact} />
  }
  if (typeId === 'shine') {
    return <ShinePreview modifications={modifications} compact={compact} />
  }
  if (typeId === 'laser_ring') {
    return <LaserRingPreview modifications={modifications} compact={compact} />
  }
  // Sword trails
  if (typeId === 'sword') {
    return <SwordPreview modifications={modifications} compact={compact} />
  }
  // 2-color effects (punch, thunder, fireball, shadow ball)
  if (typeId === 'falcon_punch' || typeId === 'warlock_punch' ||
      typeId === 'thunder' || typeId === 'pk_thunder' ||
      typeId === 'fireball' || typeId === 'shadow_ball') {
    return <DualColorPreview extraType={extraType} modifications={modifications} compact={compact} />
  }
  // Fallback to laser for unknown types
  console.warn('[ExtraPreview] Unknown extra type:', typeId)
  return <LaserBeamPreview modifications={modifications} compact={compact} />
}

// Convert currentColors (object from API) to modifications format for preview
export const currentColorsToMods = (colors) => {
  if (!colors) return null
  const mods = {}
  for (const [key, value] of Object.entries(colors)) {
    mods[key] = { color: value }
  }
  return mods
}
