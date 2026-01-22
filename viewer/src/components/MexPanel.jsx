import React, { useState, useEffect } from 'react'
import './MexPanel.css'
import IsoBuilder from './IsoBuilder'
import ProjectSelector from './mex/ProjectSelector'
import CharacterMode from './mex/CharacterMode'
import StageMode from './mex/StageMode'

const MexPanel = () => {
  const [mode, setMode] = useState('characters')
  const [mexStatus, setMexStatus] = useState(null)
  const [fighters, setFighters] = useState([])
  const [selectedFighter, setSelectedFighter] = useState(null)
  const [storageCostumes, setStorageCostumes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [projectLoaded, setProjectLoaded] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [showIsoBuilder, setShowIsoBuilder] = useState(false)
  const [showProjectModal, setShowProjectModal] = useState(false)

  const API_URL = 'http://127.0.0.1:5000/api/mex'

  useEffect(() => {
    fetchMexStatus()
  }, [])

  useEffect(() => {
    if (projectLoaded) {
      fetchFighters()
      fetchStorageCostumes()
    }
  }, [projectLoaded])

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

  const handleProjectOpened = async () => {
    await fetchMexStatus()
    setRefreshing(true)
    await Promise.all([
      fetchFighters(),
      fetchStorageCostumes()
    ])
    setRefreshing(false)
    setSelectedFighter(null)
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await Promise.all([
      fetchFighters(),
      fetchStorageCostumes()
    ])
    setRefreshing(false)
  }

  if (loading) {
    return <div className="mex-panel loading">Loading MEX Manager...</div>
  }

  if (error) {
    return (
      <div className="mex-panel error">
        <h2>MEX Connection Error</h2>
        <p>{error}</p>
        <p>Make sure the backend is running:</p>
        <code>python backend/mex_api.py</code>
      </div>
    )
  }

  // Show project selection screen if no project is loaded
  if (!projectLoaded) {
    return (
      <ProjectSelector
        showModal={false}
        onProjectOpened={handleProjectOpened}
        API_URL={API_URL}
      />
    )
  }

  return (
    <div className="mex-panel">
      <div className="mex-header">
        <div className="header-left">
          {mexStatus?.connected && (
            <div className="mex-status connected">
              <span className="status-dot"></span>
              <span>{mexStatus.project.path?.split(/[/\\]/).slice(-2, -1)[0] || mexStatus.project.name}</span>
            </div>
          )}
          <div className="action-buttons-group">
            <button
              className="action-btn export-btn"
              onClick={() => setShowIsoBuilder(true)}
            >
              Export ISO
            </button>
            <button
              className="action-btn"
              onClick={() => setShowProjectModal(true)}
            >
              Switch Project
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
      ) : (
        <StageMode
          mode={mode}
          onModeChange={setMode}
          onRefresh={handleRefresh}
          refreshing={refreshing}
          API_URL={API_URL}
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
          API_URL={API_URL}
        />
      )}
    </div>
  )
}

export default MexPanel
