import { useEffect, useRef, useState } from 'react'
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
import PoseCard from './posemanager/PoseCard'
import SavePoseControls from './posemanager/SavePoseControls'
import { POSE_MANAGER_STYLES } from './posemanager/poseManagerStyles'
import { playSound } from '../../utils/sounds'

/**
 * Pose Manager Modal - two views:
 *
 * Library (default): grid of saved poses. Click one to batch-render portraits
 * with it (PoseSkinSelectorModal), or hit "Create New Pose". Lightweight - the
 * native 3D viewer is NOT loaded here.
 *
 * Create: embedded 3D viewer + animation browser + save controls. The viewer
 * only mounts in this view; saving a pose returns to the library.
 */
export default function PoseManagerModal({
  show,
  character,
  // Custom characters: `character` is a pseudo key
  // ('custom_characters/<slug>/costumes'); pass their display name and the
  // base costume id so the create-view viewer can load the model from the
  // vault instead of a vanilla costume code.
  displayName,
  baseSkinId,
  onClose,
  onRefresh,
  onCostumesUpdated,
  API_URL
}) {
  const viewerRef = useRef(null)
  const [mode, setMode] = useState('library') // 'library' | 'create'

  // Viewer coordination: animation list polling + load-animation calls
  // (only active while the create view has the viewer mounted)
  const animations = useViewerAnimations({ show: show && mode === 'create', viewerRef })

  // Pose list management + save/delete API calls
  const poseLibrary = usePoseLibrary({ show, character, API_URL, viewerRef })

  const {
    poses,
    loadingPoses,
    selectedPose,
    setSelectedPose,
    handleDeletePose,
    saveSuccess
  } = poseLibrary

  // Always open on the library view
  useEffect(() => {
    if (show) setMode('library')
  }, [show])

  // A successful save returns to the library, where the new pose now shows
  useEffect(() => {
    if (saveSuccess) setMode('library')
  }, [saveSuccess])

  if (!show) return null

  const isCreating = mode === 'create'

  const modal = (
    <div className="pm-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`pm-modal ${isCreating ? 'pm-modal--create' : 'pm-modal--library'}`}>
        {/* Header */}
        <div className="pm-header">
          <div className="pm-title">
            {isCreating && (
              <button
                className="pm-back-btn"
                onClick={() => { playSound('back'); setMode('library'); }}
              >
                ← Poses
              </button>
            )}
            <span className="pm-title-label">{isCreating ? 'Create Pose' : 'Poses'}</span>
            <span className="pm-title-char">{displayName || character}</span>
          </div>
          <button className="pm-close-btn" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        {isCreating ? (
          <>
            {/* Create view: viewer + animation browser */}
            <div className="pm-body">
              <div className="pm-left-section">
                <div className="pm-viewer-section">
                  <EmbeddedModelViewer
                    ref={viewerRef}
                    character={character}
                    skinId={baseSkinId || undefined}
                    costumeCode={baseSkinId ? undefined : getDefaultCostumeCode(character)}
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

              {animations.animList.length > 0 && (
                <AnimationListPanel animations={animations} />
              )}
            </div>

            {/* Save controls + status messages */}
            <SavePoseControls poseLibrary={poseLibrary} />
          </>
        ) : (
          /* Library view: saved poses grid + create card */
          <div className="pm-library">
            <div className="pm-library-hint">
              Click a pose to render portraits from it, or create a new one.
            </div>
            {saveSuccess && (
              <div className="pm-message pm-success">Pose saved!</div>
            )}
            <div className="pm-library-grid">
              <div
                className="pm-create-card"
                onClick={() => { playSound('start'); setMode('create'); }}
              >
                <span className="pm-create-icon">+</span>
                <span>Create New Pose</span>
              </div>
              {loadingPoses ? (
                <div className="pm-library-empty">Loading poses…</div>
              ) : (
                poses.map(pose => (
                  <PoseCard
                    key={pose.name}
                    pose={pose}
                    character={character}
                    onDelete={handleDeletePose}
                    onClick={() => { playSound('boop'); setSelectedPose(pose); }}
                    API_URL={API_URL}
                  />
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Skin Selector Modal for batch CSP generation (opens from the library) */}
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
