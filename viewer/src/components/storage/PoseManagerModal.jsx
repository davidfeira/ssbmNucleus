import { useRef } from 'react'
import { createPortal } from 'react-dom'
import EmbeddedModelViewer from '../EmbeddedModelViewer'
import PoseSkinSelectorModal from './PoseSkinSelectorModal'
import { getAppContentPortalTarget } from './appContentPortal'
import { CloseIcon } from '../shared/Icons'
import { getDefaultCostumeCode } from './posemanager/animData'
import useViewerAnimations from './posemanager/useViewerAnimations'
import usePoseLibrary from './posemanager/usePoseLibrary'
import CategoryBar from './posemanager/CategoryBar'
import AnimationListPanel from './posemanager/AnimationListPanel'
import SavedPosesPanel from './posemanager/SavedPosesPanel'
import SavePoseControls from './posemanager/SavePoseControls'
import { POSE_MANAGER_STYLES } from './posemanager/poseManagerStyles'

/**
 * Pose Manager Modal
 * Allows users to pose characters and save poses for CSP generation
 * Left side: 3D viewer for posing + category buttons
 * Middle: Animation list with human-readable names
 * Right side: Grid of saved poses with thumbnails
 */
export default function PoseManagerModal({
  show,
  character,
  onClose,
  onRefresh,
  onCostumesUpdated,
  API_URL
}) {
  const viewerRef = useRef(null)

  // Viewer coordination: animation list polling + load-animation calls
  const animations = useViewerAnimations({ show, viewerRef })

  // Pose list management + save/delete API calls
  const poseLibrary = usePoseLibrary({ show, character, API_URL, viewerRef })

  const { selectedPose, setSelectedPose } = poseLibrary

  if (!show) return null

  const modal = (
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
                  inline={true}
                  cspMode={true}
                  showGrid={false}
                  showBackground={false}
                />
              </div>

              {/* Category buttons below viewer */}
              <CategoryBar animations={animations} />
            </div>
          )}

          {/* Middle: Animation List (bigger) */}
          {!selectedPose && animations.animList.length > 0 && (
            <AnimationListPanel animations={animations} />
          )}

          {/* Right: Saved Poses (smaller) */}
          <SavedPosesPanel
            character={character}
            API_URL={API_URL}
            poseLibrary={poseLibrary}
          />
        </div>

        {/* Save controls + status messages */}
        <SavePoseControls poseLibrary={poseLibrary} />
      </div>

      {/* Skin Selector Modal for batch CSP generation */}
      <PoseSkinSelectorModal
        show={selectedPose !== null}
        character={character}
        poseName={selectedPose?.name}
        poseThumbnail={selectedPose?.hasThumbnail ? `${API_URL.replace('/api/mex', '')}${selectedPose.thumbnailUrl}` : null}
        onClose={() => setSelectedPose(null)}
        onRefresh={onRefresh}
        onCostumesUpdated={onCostumesUpdated}
        API_URL={API_URL}
      />

      <style>{POSE_MANAGER_STYLES}</style>
    </div>
  )

  const portalTarget = getAppContentPortalTarget()
  return portalTarget ? createPortal(modal, portalTarget) : modal
}
