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
  // Optional list of models to choose from in the create view:
  // [{ value, label, skinId? , costumeCode? }]. Falls back to baseSkinId /
  // the default costume code when omitted.
  models,
  onClose,
  onRefresh,
  onCostumesUpdated,
  // When set, clicking a library pose calls this instead of opening the
  // batch skin selector (used by the install page's apply-to-all flow)
  onSelectPose,
  API_URL
}) {
  const viewerRef = useRef(null)
  const [mode, setMode] = useState('library') // 'library' | 'create'
  // Which model the create-view viewer loads (#2). null => default/baseSkinId.
  const [selectedModelValue, setSelectedModelValue] = useState(null)
  // "Start from existing pose" (#3): {sceneFile, animSymbol, frame, poseName}.
  const [startFrom, setStartFrom] = useState(null)

  const modelList = Array.isArray(models) ? models : []
  const selectedModel =
    modelList.find(m => m.value === selectedModelValue) ||
    modelList.find(m => m.skinId && m.skinId === baseSkinId) ||
    modelList[0] || null

  // Fetch a saved pose's viewer scene file + animation, then open the create
  // view starting from it.
  const startFromPose = async (pose) => {
    try {
      const res = await fetch(
        `${API_URL}/storage/poses/scene-file/${encodeURIComponent(character)}/${encodeURIComponent(pose.name)}`)
      const data = await res.json()
      if (!data.success) throw new Error(data.error || 'Failed to load pose')
      setStartFrom({ sceneFile: data.sceneFile, animSymbol: data.animSymbol,
                     frame: data.frame, poseName: pose.name })
      playSound('start')
      setMode('create')
    } catch (err) {
      console.error('[PoseManager] start-from-pose error:', err)
    }
  }

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
    if (show) { setMode('library'); setStartFrom(null); setSelectedModelValue(null) }
  }, [show])

  // A successful save returns to the library, where the new pose now shows
  useEffect(() => {
    if (saveSuccess) { setMode('library'); setStartFrom(null) }
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
                {/* Model picker sits in a LEFT column, not above the viewer:
                    the native HSD render window is an OS-topmost overlay over
                    the viewport, so a dropdown opening down over it would be
                    occluded. Keeping it left of the viewport avoids that. */}
                <div className="pm-create-row">
                  {modelList.length > 1 && (
                    <div className="pm-model-select">
                      <label>Model</label>
                      <select
                        value={selectedModel?.value ?? ''}
                        onChange={(e) => { playSound('boop'); setSelectedModelValue(e.target.value) }}
                      >
                        {modelList.map(m => (
                          <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                      </select>
                      {startFrom && (
                        <span className="pm-startfrom-tag">from “{startFrom.poseName}”</span>
                      )}
                    </div>
                  )}
                  <div className="pm-viewer-section">
                    <EmbeddedModelViewer
                      key={`${selectedModel?.value || baseSkinId || 'default'}|${startFrom?.poseName || 'new'}`}
                      ref={viewerRef}
                      character={character}
                      skinId={selectedModel ? (selectedModel.skinId || undefined) : (baseSkinId || undefined)}
                      costumeCode={selectedModel
                        ? (selectedModel.skinId ? undefined : selectedModel.costumeCode)
                        : (baseSkinId ? undefined : getDefaultCostumeCode(character))}
                      overrideSceneFile={startFrom?.sceneFile || null}
                      startAnimSymbol={startFrom?.animSymbol || null}
                      startFrame={startFrom?.frame || 0}
                      onClose={onClose}
                      inline={true}
                      cspMode={true}
                      showGrid={false}
                      showBackground={false}
                    />
                  </div>
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
              {onSelectPose
                ? 'Click a pose to apply it to all installed costumes, or create a new one.'
                : 'Click a pose to render portraits from it, or create a new one.'}
            </div>
            {saveSuccess && (
              <div className="pm-message pm-success">Pose saved!</div>
            )}
            <div className="pm-library-grid">
              <div
                className="pm-create-card"
                onClick={() => { playSound('start'); setStartFrom(null); setMode('create'); }}
              >
                <span className="pm-create-icon">+</span>
                <span>Create New Pose</span>
              </div>
              {onSelectPose && (
                <div
                  className="pm-create-card pm-original-card"
                  onClick={() => { playSound('boop'); onSelectPose({ name: '__original__', isOriginal: true }); }}
                  title="Put every installed costume's portrait back to its original CSP"
                >
                  <span className="pm-create-icon">↩</span>
                  <span>Original Portraits</span>
                </div>
              )}
              {loadingPoses ? (
                <div className="pm-library-empty">Loading poses…</div>
              ) : (
                poses.map(pose => (
                  <PoseCard
                    key={pose.name}
                    pose={pose}
                    character={character}
                    onDelete={handleDeletePose}
                    onClick={() => {
                      if (onSelectPose) { onSelectPose(pose); return }
                      playSound('boop'); setSelectedPose(pose)
                    }}
                    onStartFrom={startFromPose}
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
