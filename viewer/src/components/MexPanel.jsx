import React, { useState, useEffect, useRef } from 'react'
import './MexPanel.css'
import { playSound, playHoverSound } from '../utils/sounds'
import IsoBuilder from './IsoBuilder'
import ProjectSelector from './mex/ProjectSelector'
import BuildInfoModal from './mex/BuildInfoModal'
import ProjectHeaderInfo from './mex/ProjectHeaderInfo'
import DiscUsageIndicator from './mex/DiscUsageIndicator'
import CharacterMode from './mex/CharacterMode'
import StageMode from './mex/StageMode'
import MenuMode from './mex/MenuMode'
import HexagonLoader from './shared/HexagonLoader'
import { API_URL } from '../config'

const MexPanel = ({ active, vaultMetadata }) => {
  const [mode, setMode] = useState('characters')
  const [mexStatus, setMexStatus] = useState(null)
  const [fighters, setFighters] = useState([])
  const [selectedFighter, setSelectedFighter] = useState(null)
  const [storageCostumes, setStorageCostumes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [diagnostics, setDiagnostics] = useState(null)
  const [projectLoaded, setProjectLoaded] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [showIsoBuilder, setShowIsoBuilder] = useState(false)
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [showBuildModal, setShowBuildModal] = useState(false)
  const [buildInfo, setBuildInfo] = useState(null)
  const [createProjectOverlay, setCreateProjectOverlay] = useState({
    active: false,
    title: 'Creating Project',
    status: '',
    progress: 0
  })

  useEffect(() => {
    fetchMexStatus()
  }, [])

  useEffect(() => {
    if (projectLoaded) {
      fetchFighters()
      fetchStorageCostumes()
      fetchBuildInfo()
    }
  }, [projectLoaded])

  // The vault (Storage tab) and this install page keep their own copies of the
  // costume list, and both panels stay mounted (just hidden). So a folder move /
  // reorder / retake done in the vault would leave our "Available to Import" list
  // stale. Re-fetch it (a) whenever this tab becomes active, and (b) the moment
  // the vault changes -- App.fetchMetadata runs on every vault mutation and hands
  // us a fresh metadata object -- so the install order always matches the vault.
  useEffect(() => {
    if (active && projectLoaded) fetchStorageCostumes()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active])

  const vaultFirstRef = useRef(true)
  useEffect(() => {
    // Skip the initial value (the projectLoaded effect already loaded the list);
    // only re-fetch on SUBSEQUENT vault changes.
    if (vaultFirstRef.current) { vaultFirstRef.current = false; return }
    if (projectLoaded) fetchStorageCostumes()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vaultMetadata])

  const fetchMexStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/status`)
      const data = await response.json()
      setMexStatus(data)
      setProjectLoaded(data.projectLoaded || false)
      setLoading(false)
    } catch (err) {
      setError('Failed to connect to MEX API')
      console.error(err)
      if (window.electron?.getBackendDiagnostics) {
        try {
          const diag = await window.electron.getBackendDiagnostics()
          setDiagnostics(diag)
        } catch (diagErr) {
          console.error('Failed to fetch backend diagnostics:', diagErr)
        }
      }
      setLoading(false)
    }
  }

  const fetchFighters = async () => {
    try {
      const response = await fetch(`${API_URL}/fighters`)
      const data = await response.json()
      if (data.success) {
        setFighters(data.fighters)
      }
    } catch (err) {
      console.error('Failed to fetch fighters:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchStorageCostumes = async () => {
    try {
      const response = await fetch(`${API_URL}/storage/costumes`)
      const data = await response.json()
      if (data.success) {
        setStorageCostumes(data.costumes)
      }
    } catch (err) {
      console.error('Failed to fetch storage costumes:', err)
    }
  }

  const fetchBuildInfo = async () => {
    try {
      const response = await fetch(`${API_URL}/project/build`)
      const data = await response.json()
      if (data.success) {
        setBuildInfo(data)
      }
    } catch (err) {
      console.error('Failed to fetch build info:', err)
    }
  }

  // Persist an inline header edit (long name / long maker) and refresh.
  const handleInlineBuildSave = async (payload) => {
    const response = await fetch(`${API_URL}/project/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const data = await response.json()
    if (!data.success) throw new Error(data.error || 'Save failed')
    playSound('boop')
    await fetchBuildInfo()
  }

  const handleProjectOpened = async () => {
    setBuildInfo(null)  // drop the previous project's banner while the new one loads
    setCreateProjectOverlay((currentState) => currentState.active
      ? {
          ...currentState,
          title: 'Loading Project Data',
          status: 'Refreshing project status and opening the new workspace...',
          progress: Math.max(currentState.progress, 97)
        }
      : currentState)

    await fetchMexStatus()
    setRefreshing(true)

    setCreateProjectOverlay((currentState) => currentState.active
      ? {
          ...currentState,
          title: 'Loading Fighters and Assets',
          status: 'Fetching fighters and available costumes for the new project...',
          progress: Math.max(currentState.progress, 99)
        }
      : currentState)

    await Promise.all([
      fetchFighters(),
      fetchStorageCostumes(),
      fetchBuildInfo()
    ])
    setRefreshing(false)
    setSelectedFighter(null)
  }

  const handleProjectDeleted = async () => {
    await fetchMexStatus()
    setSelectedFighter(null)
    setShowProjectModal(false)
  }

  const handleCloseProject = async () => {
    try {
      const response = await fetch(`${API_URL}/project/close`, {
        method: 'POST'
      })
      const data = await response.json()

      if (!data.success) {
        alert(`Failed to close project: ${data.error}`)
        return
      }

      await fetchMexStatus()
      setSelectedFighter(null)
      setShowProjectModal(false)
      setShowIsoBuilder(false)
    } catch (err) {
      alert(`Error closing project: ${err.message}`)
    }
  }

  const handleOpenProjectFolder = async () => {
    if (!mexStatus?.project?.path) {
      return
    }

    if (!window.electron?.openProjectFolder) {
      alert('Electron API not available. Please run this app in Electron mode.')
      return
    }

    try {
      const result = await window.electron.openProjectFolder(mexStatus.project.path)
      if (!result?.success) {
        alert(`Failed to open project folder: ${result?.error || 'Unknown error'}`)
      }
    } catch (err) {
      alert(`Error opening project folder: ${err.message}`)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await Promise.all([
      fetchFighters(),
      fetchStorageCostumes()
    ])
    setRefreshing(false)
  }

  const renderCreateProjectOverlay = () => {
    if (!createProjectOverlay.active) {
      return null
    }

    return (
      <div className="import-overlay">
        <div className="import-modal import-modal--hexagon">
          <HexagonLoader
            size={116}
            className="import-loader"
            progress={createProjectOverlay.progress}
            label={`Creating project. ${createProjectOverlay.status || 'Working...'}`}
          />
          <h3>{createProjectOverlay.title}</h3>
          <p className="import-status">{createProjectOverlay.status}</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return <div className="mex-panel loading">Loading MEX Manager...</div>
  }

  if (error) {
    const recentOutput = diagnostics?.output?.slice(-20).join('\n')
    return (
      <div className="mex-panel error">
        <h2>MEX Connection Error</h2>
        <p>{error}</p>
        {diagnostics?.startupError && (
          <>
            <p>The bundled backend failed to start:</p>
            <code>{diagnostics.startupError}</code>
          </>
        )}
        {recentOutput && (
          <details className="mex-error-details">
            <summary>Show backend output (paste this when reporting the issue)</summary>
            <pre className="mex-error-log">{recentOutput}</pre>
          </details>
        )}
        {!window.electron && (
          <>
            <p>Make sure the backend is running:</p>
            <code>python backend/mex_api.py</code>
          </>
        )}
      </div>
    )
  }

  // Show project selection screen if no project is loaded
  if (!projectLoaded) {
    return (
      <>
        <ProjectSelector
          showModal={false}
          onProjectOpened={handleProjectOpened}
          onProjectDeleted={handleProjectDeleted}
          onCreateProjectOverlayChange={setCreateProjectOverlay}
          API_URL={API_URL}
        />
        {renderCreateProjectOverlay()}
      </>
    )
  }

  return (
    <>
      <div className="mex-panel">
        <div className="mex-header">
          <div className="header-left">
            {mexStatus?.connected && (
              <ProjectHeaderInfo
                buildInfo={buildInfo}
                projectName={mexStatus.project.path?.split(/[/\\]/).slice(-2, -1)[0] || mexStatus.project.name}
                onOpenBanner={() => setShowBuildModal(true)}
                onSaveField={handleInlineBuildSave}
              />
            )}
            {mexStatus?.connected && projectLoaded && (
              <DiscUsageIndicator
                API_URL={API_URL}
                projectLoaded={projectLoaded}
                totalCostumes={(fighters || []).reduce((s, f) => s + (f.costumeCount || 0), 0)}
              />
            )}
            <div className="action-buttons-group">
              <button
                className="action-btn"
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('start'); handleOpenProjectFolder() }}
              >
                Open Folder
              </button>
              <button
                className="action-btn close-project-btn"
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('back'); handleCloseProject() }}
              >
                Close Project
              </button>
              <button
                className="action-btn"
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('start'); setShowProjectModal(true); }}
              >
                Switch Project
              </button>
              <button
                className="action-btn export-btn"
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('start'); setShowIsoBuilder(true); }}
              >
                Export
              </button>
            </div>
          </div>
        </div>

        {mode === 'characters' ? (
          <CharacterMode
            mode={mode}
            onModeChange={setMode}
            fighters={fighters}
            selectedFighter={selectedFighter}
            onSelectFighter={setSelectedFighter}
            storageCostumes={storageCostumes}
            onRefresh={handleRefresh}
            refreshing={refreshing}
            API_URL={API_URL}
          />
        ) : mode === 'stages' ? (
          <StageMode
            mode={mode}
            onModeChange={setMode}
            onRefresh={handleRefresh}
            refreshing={refreshing}
            API_URL={API_URL}
          />
        ) : (
          <MenuMode
            mode={mode}
            onModeChange={setMode}
          />
        )}

        {showIsoBuilder && (
          <IsoBuilder
            onClose={() => setShowIsoBuilder(false)}
            projectName={mexStatus?.project?.path?.split(/[/\\]/).slice(-2, -1)[0] || 'game'}
          />
        )}

        {showProjectModal && (
          <ProjectSelector
            showModal={true}
            onClose={() => setShowProjectModal(false)}
            onProjectOpened={handleProjectOpened}
            onProjectDeleted={handleProjectDeleted}
            onCreateProjectOverlayChange={setCreateProjectOverlay}
            API_URL={API_URL}
          />
        )}

        <BuildInfoModal
          show={showBuildModal}
          onClose={() => { setShowBuildModal(false); fetchBuildInfo() }}
          API_URL={API_URL}
        />
      </div>

      {renderCreateProjectOverlay()}
    </>
  )
}

export default MexPanel
