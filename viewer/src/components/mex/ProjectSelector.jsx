/**
 * ProjectSelector - MEX project selection and management
 *
 * Features:
 * - Unified project catalog for managed and external projects
 * - Open existing .mexproj file
 * - Create new project from vanilla ISO
 * - Project switching modal
 */
import { useEffect, useRef, useState } from 'react'
import { playSound, playHoverSound } from '../../utils/sounds'
import HexagonLoader from '../shared/HexagonLoader'

const EXTERNAL_PROJECTS_STORAGE_KEY = 'mex_external_projects'
const LEGACY_PROJECTS_STORAGE_KEY = 'mex_recent_projects'
const LEGACY_KNOWN_PROJECTS_STORAGE_KEY = 'mex_known_projects'

export default function ProjectSelector({
  showModal,
  onClose,
  onProjectOpened,
  onProjectDeleted,
  onCreateProjectOverlayChange,
  API_URL
}) {
  const [projects, setProjects] = useState([])
  const [projectsLoading, setProjectsLoading] = useState(true)
  const [projectsError, setProjectsError] = useState('')
  const [openingProject, setOpeningProject] = useState(false)
  const [creatingProject, setCreatingProject] = useState(false)
  const [deletingProjectPath, setDeletingProjectPath] = useState('')
  const [createProjectTitle, setCreateProjectTitle] = useState('Creating Project')
  const [createProjectStatus, setCreateProjectStatus] = useState('')
  const [createProjectProgress, setCreateProjectProgress] = useState(0)
  const [showCreateProjectNameModal, setShowCreateProjectNameModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('My Project')
  const [createProjectNameError, setCreateProjectNameError] = useState('')
  const createProjectNameInputRef = useRef(null)

  const syncCreateProjectOverlay = (nextState) => {
    const overlayState = {
      active: false,
      title: 'Creating Project',
      status: '',
      progress: 0,
      ...nextState
    }

    if (!onCreateProjectOverlayChange) {
      setCreateProjectTitle(overlayState.title)
      setCreateProjectStatus(overlayState.status)
      setCreateProjectProgress(overlayState.progress)
    }
    onCreateProjectOverlayChange?.(overlayState)
  }

  const clearCreateProjectOverlay = () => {
    syncCreateProjectOverlay({
      active: false,
      title: 'Creating Project',
      status: '',
      progress: 0
    })
  }

  function inferManagedProjectFromPath(projectPath) {
    if (!projectPath) {
      return false
    }

    return /[\\/]projects[\\/][^\\/]+[\\/][^\\/]+\.mexproj$/i.test(projectPath)
  }

  function getProjectDisplayName(project) {
    return project.path?.split(/[/\\]/).slice(-2, -1)[0] || project.name
  }

  function getProjectDirectory(project) {
    if (project.projectDirectory) {
      return project.projectDirectory
    }

    return project.path?.replace(/[\\/][^\\/]+$/, '') || ''
  }

  function isManagedProject(project) {
    if (typeof project.isManagedProject === 'boolean') {
      return project.isManagedProject
    }

    return inferManagedProjectFromPath(project.path)
  }

  function normalizeProjectRecord(project) {
    if (!project?.path) {
      return null
    }

    const lastOpenedAt = Number.isFinite(project.lastOpenedAt)
      ? project.lastOpenedAt
      : Number.isFinite(project.timestamp)
        ? project.timestamp
        : 0

    const lastModifiedAt = Number.isFinite(project.lastModifiedAt)
      ? project.lastModifiedAt
      : 0

    return {
      path: project.path,
      name: project.name || project.path?.split(/[/\\]/).slice(-2, -1)[0] || 'Project',
      projectDirectory: project.projectDirectory || project.path.replace(/[\\/][^\\/]+$/, ''),
      isManagedProject: typeof project.isManagedProject === 'boolean'
        ? project.isManagedProject
        : inferManagedProjectFromPath(project.path),
      isCurrentProject: Boolean(project.isCurrentProject),
      lastOpenedAt,
      lastModifiedAt
    }
  }

  function compareProjects(left, right) {
    if (left.isCurrentProject !== right.isCurrentProject) {
      return left.isCurrentProject ? -1 : 1
    }

    if (left.lastOpenedAt !== right.lastOpenedAt) {
      return right.lastOpenedAt - left.lastOpenedAt
    }

    if (left.lastModifiedAt !== right.lastModifiedAt) {
      return right.lastModifiedAt - left.lastModifiedAt
    }

    return getProjectDisplayName(left).localeCompare(getProjectDisplayName(right), undefined, { sensitivity: 'base' })
  }

  function mergeProjectCollections(externalProjects, managedProjects) {
    const projectMap = new Map()

    externalProjects
      .map(normalizeProjectRecord)
      .filter(Boolean)
      .forEach((project) => {
        projectMap.set(project.path, project)
      })

    managedProjects
      .map(normalizeProjectRecord)
      .filter(Boolean)
      .forEach((project) => {
        const savedProject = projectMap.get(project.path)

        projectMap.set(project.path, {
          ...savedProject,
          ...project,
          name: savedProject?.name || project.name,
          lastOpenedAt: savedProject?.lastOpenedAt || project.lastOpenedAt
        })
      })

    return Array.from(projectMap.values()).sort(compareProjects)
  }

  function writeStoredProjects(projectEntries) {
    try {
      const normalizedProjects = projectEntries
        .map(normalizeProjectRecord)
        .filter(Boolean)
        .filter((project) => !isManagedProject(project))
        .sort(compareProjects)
        .map((project) => ({
          path: project.path,
          name: project.name,
          projectDirectory: project.projectDirectory,
          isManagedProject: false,
          lastOpenedAt: project.lastOpenedAt,
          lastModifiedAt: project.lastModifiedAt
        }))

      localStorage.setItem(EXTERNAL_PROJECTS_STORAGE_KEY, JSON.stringify(normalizedProjects))
      localStorage.removeItem(LEGACY_KNOWN_PROJECTS_STORAGE_KEY)
      localStorage.removeItem(LEGACY_PROJECTS_STORAGE_KEY)
    } catch (err) {
      console.error('Failed to save external projects:', err)
    }
  }

  function readStoredProjects() {
    try {
      const storedProjects = localStorage.getItem(EXTERNAL_PROJECTS_STORAGE_KEY)
      const legacyKnownProjects = localStorage.getItem(LEGACY_KNOWN_PROJECTS_STORAGE_KEY)
      const legacyProjects = localStorage.getItem(LEGACY_PROJECTS_STORAGE_KEY)
      const rawProjects = storedProjects || legacyKnownProjects || legacyProjects

      if (!rawProjects) {
        return []
      }

      const parsedJson = JSON.parse(rawProjects)
      const parsedProjects = Array.isArray(parsedJson)
        ? parsedJson
        : []

      const normalizedProjects = parsedProjects
        .map(normalizeProjectRecord)
        .filter(Boolean)
        .filter((project) => !isManagedProject(project))
        .sort(compareProjects)

      const shouldRewriteStorage = !storedProjects
        || Boolean(legacyKnownProjects)
        || Boolean(legacyProjects)
        || normalizedProjects.length !== parsedProjects.length

      if (shouldRewriteStorage) {
        writeStoredProjects(normalizedProjects)
      }

      return normalizedProjects
    } catch (err) {
      console.error('Failed to load saved external projects:', err)
      return []
    }
  }

  function rememberProject(projectPath, projectName, projectMeta = {}) {
    const projectIsManaged = typeof projectMeta.isManagedProject === 'boolean'
      ? projectMeta.isManagedProject
      : inferManagedProjectFromPath(projectPath)

    if (projectIsManaged) {
      forgetProject(projectPath)
      return
    }

    const storedProjects = readStoredProjects().filter((project) => project.path !== projectPath)

    storedProjects.unshift({
      path: projectPath,
      name: projectName,
      projectDirectory: projectMeta.projectDirectory || projectPath?.replace(/[\\/][^\\/]+$/, ''),
      isManagedProject: false,
      lastOpenedAt: Date.now(),
      lastModifiedAt: projectMeta.lastModifiedAt || 0
    })

    writeStoredProjects(storedProjects)
  }

  function forgetProject(projectPath) {
    const storedProjects = readStoredProjects().filter((project) => project.path !== projectPath)
    writeStoredProjects(storedProjects)
  }

  async function loadProjects() {
    const storedProjects = readStoredProjects()

    setProjectsLoading(true)
    setProjectsError('')

    try {
      const response = await fetch(`${API_URL}/project/list`)
      const data = await response.json()

      if (!data.success) {
        throw new Error(data.error || 'Failed to load projects')
      }

      setProjects(mergeProjectCollections(storedProjects, data.projects || []))
    } catch (err) {
      console.error('Failed to load project catalog:', err)
      setProjects(mergeProjectCollections(storedProjects, []))
      setProjectsError(
        storedProjects.length > 0
          ? 'Could not refresh managed projects. Showing saved external projects only.'
          : 'Could not load the project list.'
      )
    } finally {
      setProjectsLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [])

  useEffect(() => {
    if (showCreateProjectNameModal) {
      requestAnimationFrame(() => {
        createProjectNameInputRef.current?.focus()
        createProjectNameInputRef.current?.select()
      })
    }
  }, [showCreateProjectNameModal])

  const handleOpenProjectFromPath = async (projectPath) => {
    setOpeningProject(true)

    try {
      console.log('Opening project:', projectPath)

      const response = await fetch(`${API_URL}/project/open`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectPath })
      })

      const data = await response.json()

      if (data.success) {
        console.log('[OK] Project opened:', data.project.name)
        rememberProject(projectPath, data.project.name, data.project)
        await onProjectOpened()
        if (onClose) {
          onClose()
        }
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
        rememberProject(filePath, data.project.name, data.project)
        await onProjectOpened()
        if (onClose) {
          onClose()
        }
      } else {
        alert(`Failed to open project: ${data.error}`)
      }
    } catch (err) {
      alert(`Error opening project: ${err.message}`)
    } finally {
      setOpeningProject(false)
    }
  }

  const openCreateProjectNameModal = () => {
    setNewProjectName('My Project')
    setCreateProjectNameError('')
    setShowCreateProjectNameModal(true)
  }

  const closeCreateProjectNameModal = () => {
    if (creatingProject) {
      return
    }

    setShowCreateProjectNameModal(false)
    setCreateProjectNameError('')
  }

  const handleCreateProject = async (projectName) => {
    if (!window.electron) {
      alert('Electron API not available. Please run this app in Electron mode.')
      return
    }

    const createProjectRequest = async (isoPath) => {
      const response = await fetch(`${API_URL}/project/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isoPath, projectName })
      })

      const data = await response.json()
      return { response, data }
    }

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

    setCreatingProject(true)
    syncCreateProjectOverlay({
      active: true,
      title: 'Creating Workspace',
      progress: 14,
      status: 'Preparing a managed project from your vanilla ISO...'
    })

    try {
      let { response, data } = await createProjectRequest(isoPath)

      if (!data.success && response.status === 404 && data.error?.includes('ISO file not found')) {
        localStorage.removeItem('vanilla_iso_path')
        syncCreateProjectOverlay({
          active: true,
          title: 'Vanilla ISO Missing',
          progress: 8,
          status: 'Saved ISO path could not be found. Select your ISO again...'
        })

        const replacementIsoPath = await window.electron.openIsoDialog()
        if (!replacementIsoPath) {
          return
        }

        isoPath = replacementIsoPath
        syncCreateProjectOverlay({
          active: true,
          title: 'Creating Workspace',
          progress: 14,
          status: 'Preparing a managed project from your vanilla ISO...'
        })
        ;({ response, data } = await createProjectRequest(isoPath))
      }

      if (!data.success) {
        alert(`Failed to create project: ${data.error}`)
        return
      }

      console.log('[OK] Project created:', data.projectPath)

      localStorage.setItem('vanilla_iso_path', isoPath)
      console.log('[OK] Saved vanilla ISO path:', isoPath)

      syncCreateProjectOverlay({
        active: true,
        title: 'Opening Project',
        progress: 56,
        status: 'Project files are ready. Opening them in Nucleus...'
      })
      const openResponse = await fetch(`${API_URL}/project/open`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ projectPath: data.projectPath })
      })

      const openData = await openResponse.json()

      if (!openData.success) {
        alert(`Project created but failed to open: ${openData.error}`)
        return
      }

      console.log('[OK] Project opened:', openData.project.name)
      rememberProject(data.projectPath, openData.project.name, {
        projectDirectory: data.projectDirectory,
        isManagedProject: data.isManagedProject,
        lastModifiedAt: Math.floor(Date.now() / 1000)
      })

      syncCreateProjectOverlay({
        active: true,
        title: 'Installing Stage Variants',
        progress: 84,
        status: 'Setting up Dynamic Alternate Stages for the new project...'
      })
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

      syncCreateProjectOverlay({
        active: true,
        title: 'Loading Project Data',
        progress: 96,
        status: 'Loading fighters, stages, and vault data...'
      })
      await onProjectOpened()
      if (onClose) {
        onClose()
      }
    } catch (err) {
      alert(`Error creating project: ${err.message}`)
    } finally {
      setCreatingProject(false)
      clearCreateProjectOverlay()
    }
  }

  const handleCreateProjectNameSubmit = async (event) => {
    event.preventDefault()

    const trimmedProjectName = newProjectName.trim()
    if (!trimmedProjectName) {
      setCreateProjectNameError('Enter a project name.')
      return
    }

    setShowCreateProjectNameModal(false)
    setCreateProjectNameError('')
    await handleCreateProject(trimmedProjectName)
  }

  const renderCreateProjectOverlay = () => {
    if (!creatingProject) {
      return null
    }

    return (
      <div className="import-overlay">
        <div className="import-modal import-modal--hexagon">
          <HexagonLoader
            size={116}
            className="import-loader"
            progress={createProjectProgress}
            label={`Creating project. ${createProjectStatus || 'Working...'}`}
          />
          <h3>{createProjectTitle}</h3>
          <p className="import-status">{createProjectStatus}</p>
        </div>
      </div>
    )
  }

  const renderCreateProjectNameModal = () => {
    if (!showCreateProjectNameModal) {
      return null
    }

    return (
      <div className="project-name-modal-overlay" onClick={closeCreateProjectNameModal}>
        <div className="project-name-modal" onClick={(event) => event.stopPropagation()}>
          <form className="project-name-form" onSubmit={handleCreateProjectNameSubmit}>
            <h3>Name New Project</h3>
            <p>Choose a name for your new project.</p>
            <input
              ref={createProjectNameInputRef}
              className="project-name-input"
              type="text"
              value={newProjectName}
              onChange={(event) => {
                setNewProjectName(event.target.value)
                if (createProjectNameError) {
                  setCreateProjectNameError('')
                }
              }}
              placeholder="Project name"
              maxLength={80}
            />
            {createProjectNameError && (
              <p className="project-name-error">{createProjectNameError}</p>
            )}
            <div className="project-name-actions">
              <button
                type="button"
                className="btn-cancel-modal"
                onMouseEnter={playHoverSound}
                onClick={() => {
                  playSound('back')
                  closeCreateProjectNameModal()
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="project-btn"
                onMouseEnter={playHoverSound}
                onClick={() => { playSound('start') }}
              >
                Create Project
              </button>
            </div>
          </form>
        </div>
      </div>
    )
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

      forgetProject(project.path)
      await loadProjects()

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

  const handleRemoveProject = async (projectPath) => {
    forgetProject(projectPath)
    await loadProjects()
  }

  const renderProjectItem = (project, idx, className) => {
    const managedProject = isManagedProject(project)
    const isDeleting = deletingProjectPath === project.path
    const itemClassName = `${className}${project.isCurrentProject ? ' project-list-item--current' : ''}`

    const managementAction = managedProject
      ? {
          className: 'recent-project-delete',
          label: isDeleting ? '...' : 'Delete',
          title: 'Delete project',
          disabled: isDeleting,
          sound: 'boop',
          onClick: () => handleDeleteProject(project)
        }
      : {
          className: 'recent-project-remove',
          label: 'Remove',
          title: 'Remove project from list',
          disabled: false,
          sound: 'boop',
          onClick: () => handleRemoveProject(project.path)
        }

    return (
      <div
        key={project.path || idx}
        className={itemClassName}
        onMouseEnter={playHoverSound}
        onClick={() => { playSound('start'); handleOpenProjectFromPath(project.path) }}
      >
        <div className="recent-project-details">
          <div className="project-entry-header">
            <div className="recent-project-name">{getProjectDisplayName(project)}</div>
            <div className="project-entry-badges">
              {project.isCurrentProject && (
                <span className="project-entry-badge project-entry-badge-current">Current</span>
              )}
            </div>
          </div>
          <div className="recent-project-path">{project.path}</div>
        </div>
        <div className="recent-project-actions">
          <button
            className="recent-project-action recent-project-open"
            onMouseEnter={playHoverSound}
            onClick={(event) => {
              event.stopPropagation()
              playSound('start')
              handleOpenProjectFolder(project)
            }}
            title="Open project folder"
          >
            Folder
          </button>
          <button
            className={`recent-project-action ${managementAction.className}`}
            onMouseEnter={playHoverSound}
            onClick={(event) => {
              event.stopPropagation()
              playSound(managementAction.sound)
              managementAction.onClick()
            }}
            title={managementAction.title}
            disabled={managementAction.disabled}
          >
            {managementAction.label}
          </button>
        </div>
      </div>
    )
  }

  const viewConfig = showModal
    ? {
        title: 'Switch Project',
        subtitle: 'Choose a project to open or create a new one.',
        subtitleClassName: 'modal-subtitle',
        headingTag: 'h2',
        projectListClassName: 'recent-projects-list-modal',
        projectItemClassName: 'recent-project-item-modal',
        projectOptionsClassName: 'project-options-modal',
        projectOptionClassName: 'project-option-modal',
        openProjectDescription: ''
      }
    : {
        title: 'Install',
        subtitle: 'Choose a project to get started.',
        subtitleClassName: 'subtitle',
        headingTag: 'h1',
        projectListClassName: 'recent-projects-list',
        projectItemClassName: 'recent-project-item',
        projectOptionsClassName: 'project-options',
        projectOptionClassName: 'project-option',
        openProjectDescription: ''
      }

  const HeadingTag = viewConfig.headingTag
  const projectCountLabel = projectsLoading && projects.length === 0
    ? 'Loading...'
    : `${projects.length} ${projects.length === 1 ? 'project' : 'projects'}`

  const projectActions = [
    {
      key: 'open-existing',
      title: 'Open Existing Project',
      description: viewConfig.openProjectDescription,
      buttonLabel: openingProject ? 'Opening...' : 'Browse for .mexproj',
      disabled: openingProject,
      onClick: handleOpenProject
    },
    {
      key: 'create-new',
      title: 'Create New Project',
      description: '',
      buttonLabel: creatingProject ? 'Creating Project...' : 'Create Project',
      disabled: creatingProject || showCreateProjectNameModal,
      onClick: openCreateProjectNameModal
    }
  ]

  const renderProjectListBody = () => {
    if (!projects.length) {
      return (
        <div className="project-list-empty">
          {projectsLoading ? 'Loading projects...' : 'No projects yet. Create a new project or browse for a .mexproj file.'}
        </div>
      )
    }

    return (
      <div className={`${viewConfig.projectListClassName} project-list-scroll`}>
        {projects.map((project, idx) => (
          renderProjectItem(project, idx, viewConfig.projectItemClassName)
        ))}
      </div>
    )
  }

  const projectManagementMenu = (
    <div className={`project-management-shell${showModal ? ' project-management-shell--modal' : ''}`}>
      <div className="project-management-header">
        <HeadingTag>{viewConfig.title}</HeadingTag>
        <p className={viewConfig.subtitleClassName}>{viewConfig.subtitle}</p>
      </div>

      <div className={`project-management-body${showModal ? ' project-management-body--modal' : ''}`}>
        <section className="project-list-panel">
          <div className="project-section-heading">
            <div>
              <h3>All Projects</h3>
              <p className="project-section-copy">Choose a project to open.</p>
            </div>
            <span className="project-list-count">{projectCountLabel}</span>
          </div>

          {projectsError && (
            <p className="project-list-notice">{projectsError}</p>
          )}

          {renderProjectListBody()}
        </section>

        <section className="project-actions-panel">
          <div className="project-section-heading">
            <div>
              <h3>Project Actions</h3>
              <p className="project-section-copy">Open an existing project or create a new one.</p>
            </div>
          </div>

          <div className={viewConfig.projectOptionsClassName}>
            {projectActions.map((action) => (
              <div key={action.key} className={viewConfig.projectOptionClassName}>
                <h3>{action.title}</h3>
                {action.description && <p>{action.description}</p>}
                <button
                  className="project-btn"
                  onMouseEnter={playHoverSound}
                  onClick={() => {
                    playSound('start')
                    action.onClick()
                  }}
                  disabled={action.disabled}
                >
                  {action.buttonLabel}
                </button>
              </div>
            ))}
          </div>

          {showModal && (
            <button
              className="btn-cancel-modal"
              onMouseEnter={playHoverSound}
              onClick={() => { playSound('back'); onClose() }}
            >
              Cancel
            </button>
          )}
        </section>
      </div>
    </div>
  )

  if (!showModal) {
    return (
      <div className="mex-panel">
        <div className="project-selection">{projectManagementMenu}</div>

        {renderCreateProjectNameModal()}
        {!onCreateProjectOverlayChange && renderCreateProjectOverlay()}
      </div>
    )
  }

  return (
    <div className="project-modal-overlay" onClick={onClose}>
      <div className="project-modal-content" onClick={(event) => event.stopPropagation()}>
        {projectManagementMenu}
      </div>

      {renderCreateProjectNameModal()}
      {!onCreateProjectOverlayChange && renderCreateProjectOverlay()}
    </div>
  )
}
