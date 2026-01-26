/**
 * ProjectSelector - MEX project selection and management
 *
 * Features:
 * - Recent projects list with remove capability
 * - Open existing .mexproj file
 * - Create new project from vanilla ISO
 * - Project switching modal
 */
import { useState, useEffect } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'

export default function ProjectSelector({
  showModal,
  onClose,
  onProjectOpened,
  API_URL
}) {
  const [recentProjects, setRecentProjects] = useState([])
  const [openingProject, setOpeningProject] = useState(false)
  const [creatingProject, setCreatingProject] = useState(false)
  const [createProjectStatus, setCreateProjectStatus] = useState('')

  // Load recent projects from localStorage
  useEffect(() => {
    loadRecentProjects()
  }, [])

  const loadRecentProjects = () => {
    try {
      const stored = localStorage.getItem('mex_recent_projects')
      if (stored) {
        const projects = JSON.parse(stored)
        setRecentProjects(projects)
      }
    } catch (err) {
      console.error('Failed to load recent projects:', err)
    }
  }

  const addToRecentProjects = (projectPath, projectName) => {
    try {
      const stored = localStorage.getItem('mex_recent_projects')
      let projects = stored ? JSON.parse(stored) : []

      // Remove if already exists
      projects = projects.filter(p => p.path !== projectPath)

      // Add to front
      projects.unshift({
        path: projectPath,
        name: projectName,
        timestamp: Date.now()
      })

      // Keep only 5 most recent
      projects = projects.slice(0, 5)

      localStorage.setItem('mex_recent_projects', JSON.stringify(projects))
      setRecentProjects(projects)
    } catch (err) {
      console.error('Failed to save recent project:', err)
    }
  }

  const removeFromRecentProjects = (projectPath) => {
    try {
      const stored = localStorage.getItem('mex_recent_projects')
      let projects = stored ? JSON.parse(stored) : []

      // Remove the specified project
      projects = projects.filter(p => p.path !== projectPath)

      localStorage.setItem('mex_recent_projects', JSON.stringify(projects))
      setRecentProjects(projects)
    } catch (err) {
      console.error('Failed to remove recent project:', err)
    }
  }

  const handleOpenProjectFromPath = async (projectPath) => {
    setOpeningProject(true)

    try {
      console.log('Opening project:', projectPath)

      const response = await fetch(`${API_URL}/project/open`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectPath: projectPath })
      })

      const data = await response.json()

      if (data.success) {
        console.log('✓ Project opened:', data.project.name)
        addToRecentProjects(projectPath, data.project.name)
        onProjectOpened()
        if (onClose) onClose()
      } else {
        alert(`Failed to open project: ${data.error}`)
      }
    } catch (err) {
      alert(`Error opening project: ${err.message}`)
    } finally {
      setOpeningProject(false)
    }
  }

  const handleOpenProject = async () => {
    if (!window.electron) {
      alert('Electron API not available. Please run this app in Electron mode.')
      return
    }

    setOpeningProject(true)

    try {
      const filePath = await window.electron.openProjectDialog()

      if (!filePath) {
        setOpeningProject(false)
        return
      }

      console.log('Selected project:', filePath)

      const response = await fetch(`${API_URL}/project/open`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectPath: filePath })
      })

      const data = await response.json()

      if (data.success) {
        console.log('✓ Project opened:', data.project.name)
        addToRecentProjects(filePath, data.project.name)
        onProjectOpened()
        if (onClose) onClose()
      } else {
        alert(`Failed to open project: ${data.error}`)
      }
    } catch (err) {
      alert(`Error opening project: ${err.message}`)
    } finally {
      setOpeningProject(false)
    }
  }

  const handleCreateProject = async () => {
    if (!window.electron) {
      alert('Electron API not available. Please run this app in Electron mode.')
      return
    }

    // Step 1: Check for saved vanilla ISO path
    let isoPath = localStorage.getItem('vanilla_iso_path')

    if (!isoPath) {
      isoPath = await window.electron.openIsoDialog()

      if (!isoPath) {
        return
      }
    } else {
      console.log('Using saved vanilla ISO path:', isoPath)
    }

    console.log('Selected ISO:', isoPath)

    // Step 2: Select project folder
    const projectDir = await window.electron.selectDirectory()

    if (!projectDir) {
      return
    }

    console.log('Selected project directory:', projectDir)
    playSound('start') // Folder selected - play start sound

    // Show loading
    setCreatingProject(true)
    setCreateProjectStatus('Creating project...')

    try {
      const projectName = 'MexProject'
      console.log('Project name:', projectName)

      // Step 3: Create project
      const response = await fetch(`${API_URL}/project/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          isoPath: isoPath,
          projectDir: projectDir,
          projectName: projectName
        })
      })

      const data = await response.json()

      if (data.success) {
        console.log('✓ Project created:', data.projectPath)

        // Save vanilla ISO path
        localStorage.setItem('vanilla_iso_path', isoPath)
        console.log('✓ Saved vanilla ISO path:', isoPath)

        // Step 4: Auto-open the project
        setCreateProjectStatus('Opening project...')
        const openResponse = await fetch(`${API_URL}/project/open`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ projectPath: data.projectPath })
        })

        const openData = await openResponse.json()

        if (openData.success) {
          console.log('✓ Project opened:', openData.project.name)
          addToRecentProjects(data.projectPath, openData.project.name)

          // Step 5: Auto-install DAS framework
          setCreateProjectStatus('Installing stage variants...')
          console.log('Installing DAS framework...')
          try {
            const dasResponse = await fetch(`${API_URL}/das/install`, {
              method: 'POST'
            })
            const dasData = await dasResponse.json()
            if (dasData.success) {
              console.log('✓ DAS framework installed')
            } else {
              console.error('DAS installation failed:', dasData.error)
            }
          } catch (dasErr) {
            console.error('DAS installation error:', dasErr)
          }

          onProjectOpened()
          if (onClose) onClose()
        } else {
          alert(`Project created but failed to open: ${openData.error}`)
        }
      } else {
        alert(`Failed to create project: ${data.error}`)
      }
    } catch (err) {
      alert(`Error creating project: ${err.message}`)
    } finally {
      setCreatingProject(false)
      setCreateProjectStatus('')
    }
  }

  // Render as initial screen (when showModal is false/undefined)
  if (!showModal) {
    return (
      <div className="mex-panel">
        <div className="project-selection">
          <h1>Install</h1>
          <p className="subtitle">Select a project to get started</p>

          {/* Recent Projects */}
          {recentProjects.length > 0 && (
            <div className="recent-projects">
              <h3>Recent Projects</h3>
              <div className="recent-projects-list">
                {recentProjects.map((project, idx) => (
                  <div
                    key={idx}
                    className="recent-project-item"
                    onMouseEnter={playHoverSound}
                    onClick={() => { playSound('start'); handleOpenProjectFromPath(project.path); }}
                  >
                    <div>
                      <div className="recent-project-name">{project.path?.split(/[/\\]/).slice(-2, -1)[0] || project.name}</div>
                      <div className="recent-project-path">{project.path}</div>
                    </div>
                    <button
                      className="recent-project-remove"
                      onMouseEnter={playHoverSound}
                      onClick={(e) => {
                        e.stopPropagation()
                        playSound('boop')
                        removeFromRecentProjects(project.path)
                      }}
                      title="Remove from recent"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="project-options">
            {/* Open existing project */}
            <div className="project-option">
              <h3>Open Existing Project</h3>
              <p>Select a .mexproj file to continue working on an existing project</p>
              <button
                className="project-btn"
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('start'); handleOpenProject(); }}
                disabled={openingProject}
              >
                {openingProject ? 'Opening...' : 'Browse for .mexproj'}
              </button>
            </div>

            {/* Create new project */}
            <div className="project-option">
              <h3>Create New Project</h3>
              <p>Provide a vanilla Melee ISO to create a new project</p>
              <button
                className="project-btn"
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('start'); handleCreateProject(); }}
                disabled={creatingProject}
              >
                {creatingProject ? 'Creating Project...' : 'Create from Vanilla ISO'}
              </button>
            </div>
          </div>
        </div>

        {/* Project Creation Loading Overlay */}
        {creatingProject && (
          <div className="import-overlay">
            <div className="import-modal">
              <div className="import-spinner"></div>
              <h3>Creating Project</h3>
              <div className="import-progress">
                <div className="import-progress-bar indeterminate" />
              </div>
              <p>{createProjectStatus}</p>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Render as modal (when showModal is true)
  return (
    <div className="project-modal-overlay" onClick={onClose}>
      <div className="project-modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>Switch Project</h2>
        <p className="modal-subtitle">Select a different project or create a new one</p>

        {/* Recent Projects in Modal */}
        {recentProjects.length > 0 && (
          <div className="recent-projects-modal">
            <h3>Recent Projects</h3>
            <div className="recent-projects-list-modal">
              {recentProjects.map((project, idx) => (
                <div
                  key={idx}
                  className="recent-project-item-modal"
                  onMouseEnter={playHoverSound}
                  onClick={() => { playSound('start'); handleOpenProjectFromPath(project.path); }}
                >
                  <div>
                    <div className="recent-project-name">{project.path?.split(/[/\\]/).slice(-2, -1)[0] || project.name}</div>
                    <div className="recent-project-path">{project.path}</div>
                  </div>
                  <button
                    className="recent-project-remove"
                    onMouseEnter={playHoverSound}
                    onClick={(e) => {
                      e.stopPropagation()
                      playSound('boop')
                      removeFromRecentProjects(project.path)
                    }}
                    title="Remove from recent"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="project-options-modal">
          {/* Open existing project */}
          <div className="project-option-modal">
            <h3>Open Existing Project</h3>
            <p>Select a .mexproj file to switch to a different project</p>
            <button
              className="project-btn"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('start'); handleOpenProject(); }}
              disabled={openingProject}
            >
              {openingProject ? 'Opening...' : 'Browse for .mexproj'}
            </button>
          </div>

          {/* Create new project */}
          <div className="project-option-modal">
            <h3>Create New Project</h3>
            <p>Provide a vanilla Melee ISO to create a new project</p>
            <button
              className="project-btn"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('start'); handleCreateProject(); }}
              disabled={creatingProject}
            >
              {creatingProject ? 'Creating Project...' : 'Create from Vanilla ISO'}
            </button>
          </div>
        </div>

        <button
          className="btn-cancel-modal"
          onMouseEnter={playHoverSound}
          onClick={() => { playSound('back'); onClose(); }}
        >
          Cancel
        </button>
      </div>

      {/* Project Creation Loading Overlay (in modal) */}
      {creatingProject && (
        <div className="import-overlay">
          <div className="import-modal">
            <div className="import-spinner"></div>
            <h3>Creating Project</h3>
            <div className="import-progress">
              <div className="import-progress-bar indeterminate" />
            </div>
            <p>{createProjectStatus}</p>
          </div>
        </div>
      )}
    </div>
  )
}
