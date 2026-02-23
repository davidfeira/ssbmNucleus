const { contextBridge, ipcRenderer } = require('electron');

// Parse backend port from Electron's additionalArguments
const backendPortArg = process.argv.find(arg => arg.startsWith('--backend-port='));
const backendPort = backendPortArg ? parseInt(backendPortArg.split('=')[1], 10) : 5000;

// Expose protected methods to the renderer process
contextBridge.exposeInMainWorld('electron', {
  /**
   * The port the Flask backend is running on (dynamic)
   */
  backendPort,

  /**
   * Open a native file picker dialog to select a .mexproj file
   * @returns {Promise<string|null>} Full file path or null if canceled
   */
  openProjectDialog: () => ipcRenderer.invoke('open-project-dialog'),

  /**
   * Open a native file picker dialog to select a vanilla Melee ISO
   * @returns {Promise<string|null>} Full file path or null if canceled
   */
  openIsoDialog: () => ipcRenderer.invoke('open-iso-dialog'),

  /**
   * Open a native directory picker dialog
   * @returns {Promise<string|null>} Full directory path or null if canceled
   */
  selectDirectory: () => ipcRenderer.invoke('select-directory-dialog'),

  /**
   * Check if running in Electron
   * @returns {boolean} Always returns true
   */
  isElectron: true,

  /**
   * Listen for nucleus:// protocol imports
   * @param {function} callback Function called with {url, name} when import is triggered
   * @returns {function} Cleanup function to remove listener
   */
  onNucleusImport: (callback) => {
    const listener = (event, data) => callback(data);
    ipcRenderer.on('nucleus-import', listener);
    // Return cleanup function
    return () => ipcRenderer.removeListener('nucleus-import', listener);
  },

  // ============================================
  // Embedded Viewer API (Named Pipe IPC)
  // ============================================

  /**
   * Start the embedded 3D viewer
   * @param {Object} options
   * @param {string} options.datFile - Path to the DAT file
   * @param {string} [options.sceneFile] - Optional scene configuration
   * @param {string} [options.ajFile] - Optional animation archive
   * @param {string} [options.logsPath] - Optional logs directory
   * @returns {Promise<{pipeName: string, hwnd: number, connected: boolean}>}
   */
  viewerStart: (options) => ipcRenderer.invoke('viewer:start', options),

  /**
   * Stop the embedded viewer
   */
  viewerStop: () => ipcRenderer.invoke('viewer:stop'),

  /**
   * Send a raw message to the viewer
   * @param {Object} message - Message object to send
   */
  viewerSend: (message) => ipcRenderer.invoke('viewer:send', message),

  /**
   * Send camera update to viewer
   */
  viewerCamera: (deltaRotX, deltaRotY, deltaZoom, deltaX, deltaY) =>
    ipcRenderer.invoke('viewer:camera', deltaRotX, deltaRotY, deltaZoom, deltaX, deltaY),

  /**
   * Request animation list from viewer
   */
  viewerGetAnimList: () => ipcRenderer.invoke('viewer:getAnimList'),

  /**
   * Load animation by symbol name
   */
  viewerLoadAnim: (symbol) => ipcRenderer.invoke('viewer:loadAnim', symbol),

  /**
   * Toggle animation playback
   */
  viewerAnimToggle: () => ipcRenderer.invoke('viewer:animToggle'),

  /**
   * Set animation frame
   */
  viewerAnimSetFrame: (frame) => ipcRenderer.invoke('viewer:animSetFrame', frame),

  /**
   * Resize/reposition the viewer window
   */
  viewerResize: (x, y, width, height) => ipcRenderer.invoke('viewer:resize', x, y, width, height),

  /**
   * Show the viewer window
   */
  viewerShow: () => ipcRenderer.invoke('viewer:show'),

  /**
   * Hide the viewer window
   */
  viewerHide: () => ipcRenderer.invoke('viewer:hide'),

  /**
   * Set CSP mode (enables special camera for character select portraits)
   */
  viewerSetCspMode: (enabled) => ipcRenderer.invoke('viewer:setCspMode', enabled),

  /**
   * Set grid visibility
   */
  viewerSetGrid: (enabled) => ipcRenderer.invoke('viewer:setGrid', enabled),

  /**
   * Set background visibility
   */
  viewerSetBackground: (enabled) => ipcRenderer.invoke('viewer:setBackground', enabled),

  /**
   * Export current scene settings (camera, frame, animation)
   */
  viewerExportScene: () => ipcRenderer.invoke('viewer:exportScene'),

  /**
   * Listen for messages from the viewer
   * @param {function} callback Function called with message data
   * @returns {function} Cleanup function to remove listener
   */
  onViewerMessage: (callback) => {
    console.log('[Preload] Setting up viewer message listener');
    const listener = (event, data) => {
      console.log('[Preload] Received viewer message:', data?.type);
      callback(data);
    };
    ipcRenderer.on('viewer:message', listener);
    return () => {
      console.log('[Preload] Removing viewer message listener');
      ipcRenderer.removeListener('viewer:message', listener);
    };
  }
});

// Log that preload script loaded successfully
console.log('[Preload] Electron API bridge initialized');
