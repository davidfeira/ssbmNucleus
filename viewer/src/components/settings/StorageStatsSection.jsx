/**
 * StorageStatsSection - Display vault storage statistics
 *
 * Features:
 * - Shows costume count across all characters
 * - Shows stage variant count
 */
export default function StorageStatsSection({ metadata }) {
  // Calculate storage statistics
  const getStorageStats = () => {
    if (!metadata) return { characterCount: 0, stageCount: 0, costumeCount: 0 }

    const characterCount = Object.keys(metadata.characters || {}).length
    let costumeCount = 0

    Object.values(metadata.characters || {}).forEach(char => {
      costumeCount += (char.skins || []).length
    })

    let stageCount = 0
    Object.values(metadata.stages || {}).forEach(stage => {
      stageCount += (stage.variants || []).length
    })

    return { characterCount, stageCount, costumeCount }
  }

  const stats = getStorageStats()

  return (
    <section className="settings-section">
      <h3>Storage Statistics</h3>
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-value">{stats.costumeCount}</div>
          <div className="stat-label">Costumes</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{stats.stageCount}</div>
          <div className="stat-label">Stage Variants</div>
        </div>
      </div>
    </section>
  )
}

// Export the stats calculation function for use by other components
export function getStorageStats(metadata) {
  if (!metadata) return { characterCount: 0, stageCount: 0, costumeCount: 0 }

  const characterCount = Object.keys(metadata.characters || {}).length
  let costumeCount = 0

  Object.values(metadata.characters || {}).forEach(char => {
    costumeCount += (char.skins || []).length
  })

  let stageCount = 0
  Object.values(metadata.stages || {}).forEach(stage => {
    stageCount += (stage.variants || []).length
  })

  return { characterCount, stageCount, costumeCount }
}
