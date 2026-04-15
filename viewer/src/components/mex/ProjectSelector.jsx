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

export default function ProjectSelector({
  showModal,
  onClose,
  onProjectOpened,
  onProjectDeleted,
  API_URL
}) {
  const [recentProjects, setRecentProjects] = useState([])
  const [openingProject, setOpeningProject] = useState(false)
  const [creatingProject, setCreatingProject] = useState(false)
  const [deletingProjectPath, setDeletingProjectPath] = useState('')
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

  const inferManagedProjectFromPath = (projectPath) => {
    if (!projectPath) {
      return false
    }

    return /[\\/]projects[\\/][^\\/]+[\\/]project\.mexproj$/i.test(projectPath)
  }

  const getProjectDisplayName = (project) => {
    return project.path?.split(/[/\\]/).slice(-2, -1)[0] || project.name
  }

  const getProjectDirectory = (project) => {
    if (project.projectDirectory) {
      return project.projectDirectory
    }

    return project.path?.replace(/[\\/][^\\/]+$/, '') || ''
  }

  const isManagedProject = (project) => {
    if (typeof project.isManagedProject === 'boolean') {
      return project.isManagedProject
    }

    return inferManagedProjectFromPath(project.path)
  }

  const addToRecentProjects = (projectPath, projectName, projectMeta = {}) => {
    try {
      const stored = localStorage.getItem('mex_recent_projects')
      let projects = stored ? JSON.parse(stored) : []

      // Remove if already exists
      projects = projects.filter(p => p.path !== projectPath)

      // Add to front
      projects.unshift({
        path: projectPath,
        name: projectName,
        projectDirectory: projectMeta.projectDirectory || projectPath?.replace(/[\\/][^\\/]+$/, ''),
        isManagedProject: typeof projectMeta.isManagedProject === 'boolean'
          ? projectMeta.isManagedProject
          : inferManagedProjectFromPath(projectPath),
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
        console.log('[OK] Project opened:', data.project.name)
        addToRecentProjects(projectPath, data.project.name, data.project)
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
        console.log('[OK] Project opened:', data.project.name)
        addToRecentProjects(filePath, data.project.name, data.project)
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

    const createProjectRequest = async (isoPath) => {
      const response = await fetch(`${API_URL}/project/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          isoPath: isoPath
        })
      })

      const data = await response.json()
      return { response, data }
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

    // Show loading
    setCreatingProject(true)
    setCreateProjectStatus('Creating project...')

    try {
      // Step 2: Create project in the app-managed projects directory
      let { response, data } = await createProjectRequest(isoPath)

      if (!data.success && response.status === 404 && data.error?.includes('ISO file not found')) {
        localStorage.removeItem('vanilla_iso_path')
        setCreateProjectStatus('Saved ISO path is missing. Select your ISO again...')

        const replacementIsoPath = await window.electron.openIsoDialog()
        if (!replacementIsoPath) {
          return
        }

        isoPath = replacementIsoPath
        setCreateProjectStatus('Creating project...')
        ;({ response, data } = await createProjectRequest(isoPath))
      }

      if (data.success) {
        console.log('[OK] Project created:', data.projectPath)
        console.log('[OK] Managed project directory:', data.projectDirectory)

        // Save vanilla ISO path
        localStorage.setItem('vanilla_iso_path', isoPath)
        console.log('[OK] Saved vanilla ISO path:', isoPath)

        // Step 3: Auto-open the project
        setCreateProjectStatus('Opening project...')
        const openResponse = await fetch(`${API_URL}/project/open`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ projectPath: data.projectPath })
        })

        const openData = await openResponse.json()

        if (openData.success) {
          console.log('[OK] Project opened:', openData.project.name)
          addToRecentProjects(data.projectPath, openData.project.name, {
            projectDirectory: data.projectDirectory,
            isManagedProject: data.isManagedProject
          })

          // Step 4: Auto-install DAS framework
          setCreateProjectStatus('Installing stage variants...')
          console.log('Installing DAS framework...')
          try {
            const dasResponse = await fetch(`${API_URL}/das/install`, {
              method: 'POST'
            })
            const dasData = await dasResponse.json()
            if (dasData.success) {
              console.log('[OK] DAS framework installed')
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

  const handleOpenProjectFolder = async (project) => {
    if (!window.electron?.openProjectFolder) {
      alert('Electron API not available. Please run this app in Electron mode.')
      return
    }

    try {
      const result = await window.electron.openProjectFolder(project.path)
      if (!result?.success) {
        alert(`Failed to open project folder: ${result?.error || 'Unknown error'}`)
      }
    } catch (err) {
      alert(`Error opening project folder: ${err.message}`)
    }
  }

  const handleDeleteProject = async (project) => {
    const projectName = getProjectDisplayName(project)
    const projectDirectory = getProjectDirectory(project)

    const confirmed = window.confirm(
      `Delete "${projectName}" and its project folder?\n\n${projectDirectory}\n\nThis cannot be undone.`
    )

    if (!confirmed) {
      return
    }

    setDeletingProjectPath(project.path)

    try {
      const response = await fetch(`${API_URL}/project/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectPath: project.path })
      })

      const data = await response.json()

      if (!data.success) {
        alert(`Failed to delete project: ${data.error}`)
        return
      }

      removeFromRecentProjects(project.path)

      if (data.currentProjectClosed && onProjectDeleted) {
        await onProjectDeleted()
      }

      if (data.currentProjectClosed && onClose) {
        onClose()
      }
    } catch (err) {
      alert(`Error deleting project: ${err.message}`)
    } finally {
      setDeletingProjectPath('')
    }
  }

  const renderRecentProjectItem = (project, idx, className) => (
    <div
      key={idx}
      className={className}
      onClick={() => handleOpenProjectFromPath(project.path)}
    >
      <div className="recent-project-details">
        <div className="recent-project-name">{getProjectDisplayName(project)}</div>
        <div className="recent-project-path">{project.path}</div>
      </div>
      <div className="recent-project-actions">
        <button
          className="recent-project-action recent-project-open"
          onClick={(e) => {
            e.stopPropagation()
            handleOpenProjectFolder(project)
          }}
          title="Open project folder"
        >
          Folder
        </button>
        {isManagedProject(project) && (
          <button
            className="recent-project-action recent-project-remove"
            onClick={(e) => {
              e.stopPropagation()
              handleDeleteProject(project)
            }}
            title="Delete project"
            disabled={deletingProjectPath === project.path}
          >
            {deletingProjectPath === project.path ? '...' : 'X'}
          </button>
        )}
      </div>
    </div>
  )

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
                  renderRecentProjectItem(project, idx, 'recent-project-item')
                ))}
              </div>
            </div>
          )}

          <div className="project-options">
            {/* Open existing project */}
            <div className="project-option">
              <h3>Open Existing Project</h3>
              <p>Select a .mexproj file to continue working on an existing MEX mod</p>
              <button
                className="project-btn"
                onClick={handleOpenProject}
                disabled={openingProject}
              >
                {openingProject ? 'Opening...' : 'Browse for .mexproj'}
              </button>
            </div>

            {/* Create new project */}
            <div className="project-option">
              <h3>Create New Project</h3>
              <p>Select your clean vanilla Melee ISO once. Nucleus will build and manage the project folder for you.</p>
              <button
                className="project-btn"
                onClick={handleCreateProject}
                disabled={creatingProject}
              >
                {creatingProject ? 'Creating Project...' : 'Create Project'}
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
                renderRecentProjectItem(project, idx, 'recent-project-item-modal')
              ))}
            </div>
          </div>
        )}

        <div className="project-options-modal">
          {/* Open existing project */}
          <div className="project-option-modal">
            <h3>Open Existing Project</h3>
            <p>Select a .mexproj file to switch to a different MEX mod</p>
            <button
              className="project-btn"
              onClick={handleOpenProject}
              disabled={openingProject}
            >
              {openingProject ? 'Opening...' : 'Browse for .mexproj'}
            </button>
          </div>

          {/* Create new project */}
          <div className="project-option-modal">
            <h3>Create New Project</h3>
            <p>Select your clean vanilla Melee ISO once. Nucleus will build and manage the project folder for you.</p>
            <button
              className="project-btn"
              onClick={handleCreateProject}
              disabled={creatingProject}
            >
              {creatingProject ? 'Creating Project...' : 'Create Project'}
            </button>
          </div>
        </div>

        <button
          className="btn-cancel-modal"
          onClick={onClose}
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
