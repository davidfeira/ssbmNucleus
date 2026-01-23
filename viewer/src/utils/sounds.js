/**
 * Melee Menu Sound Effects
 * Preloads and plays menu sounds from vanilla Melee assets
 */

// Default volume (0.0 to 1.0)
const DEFAULT_VOLUME = 0.3

// Preload and cache audio instances
const sounds = {
  back: new Audio('/vanilla/sounds/back.wav'),
  start: new Audio('/vanilla/sounds/start.wav'),
  tick: new Audio('/vanilla/sounds/tick.wav'),
  boop: new Audio('/vanilla/sounds/click.wav'),
  error: new Audio('/vanilla/sounds/error.wav'),
  camera: new Audio('/vanilla/sounds/camera_click.wav'),
  newSkin: new Audio('/vanilla/sounds/new_skin.wav'),
  achievement: new Audio('/vanilla/sounds/big_achievement.wav'),
}

// Preload all sounds and set default volume
Object.values(sounds).forEach(s => {
  s.load()
  s.volume = DEFAULT_VOLUME
})

// Achievement sound is quieter
sounds.achievement.volume = 0.2

// Hover debounce - prevent tick spam on rapid hovers
let lastHoverTime = 0
const HOVER_DEBOUNCE_MS = 50

/**
 * Play a menu sound effect
 * @param {'back'|'start'|'tick'|'error'|'camera'|'newSkin'} name - Sound name to play
 */
export const playSound = (name) => {
  const sound = sounds[name]
  if (sound) {
    sound.currentTime = 0
    sound.play().catch(() => {}) // Ignore autoplay restrictions
  }
}

/**
 * Play tick sound on hover (debounced to prevent spam)
 */
export const playHoverSound = () => {
  const now = Date.now()
  if (now - lastHoverTime > HOVER_DEBOUNCE_MS) {
    lastHoverTime = now
    playSound('tick')
  }
}
