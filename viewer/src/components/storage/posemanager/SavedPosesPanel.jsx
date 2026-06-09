import PoseCard from './PoseCard'

// Right: Saved Poses (smaller)
export default function SavedPosesPanel({ character, API_URL, poseLibrary }) {
  const { poses, loadingPoses, setSelectedPose, handleDeletePose } = poseLibrary

  return (
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
  )
}
