/**
 * Viewer Manager - Manages the embedded HSDRawViewer process
 * Uses Named Pipes for fast IPC instead of WebSocket
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const net = require('net');

class ViewerManager {
  constructor() {
    this.process = null;
    this.pipeName = null;
    this.pipeClient = null;
    this.messageBuffer = '';
    this.messageHandlers = new Map();
    this.isConnected = false;
    this.hwnd = null;
  }

  /**
   * Generate a unique pipe name
   */
  generatePipeName() {
    return `HSDViewer_${process.pid}_${Date.now()}`;
  }

  /**
   * Get the path to HSDRawViewer.exe
   */
  getViewerPath(isDev) {
    if (isDev) {
      // Development: use the built version in the tools directory
      return path.join(
        __dirname, '..',
        'utility', 'website', 'backend', 'tools',
        'HSDLib', 'HSDRawViewer', 'bin', 'Release', 'net6.0-windows',
        'HSDRawViewer.exe'
      );
    } else {
      // Production: bundled in resources
      return path.join(
        process.resourcesPath,
        'utility', 'website', 'backend', 'tools',
        'HSDLib', 'HSDRawViewer', 'bin', 'Release', 'net6.0-windows',
        'HSDRawViewer.exe'
      );
    }
  }

  /**
   * Start the embedded viewer
   * @param {Object} options
   * @param {string} options.datFile - Path to the DAT file
   * @param {string} [options.sceneFile] - Optional path to scene.yml
   * @param {string} [options.ajFile] - Optional path to AJ file for animations
   * @param {string} [options.logsPath] - Optional path for logs
   * @param {boolean} options.isDev - Whether running in development mode
   */
  async start(options) {
    const { datFile, sceneFile, ajFile, logsPath, isDev } = options;

    // Stop any existing viewer
    if (this.process) {
      await this.stop();
    }

    // Get viewer path
    const viewerPath = this.getViewerPath(isDev);
    console.log('[ViewerManager] Viewer path:', viewerPath);

    if (!fs.existsSync(viewerPath)) {
      throw new Error(`HSDRawViewer not found at: ${viewerPath}`);
    }

    // Generate unique pipe name
    this.pipeName = this.generatePipeName();
    console.log('[ViewerManager] Pipe name:', this.pipeName);

    // Build command arguments
    const args = ['--embedded', this.pipeName, datFile];
    if (logsPath) args.push(logsPath);
    if (sceneFile) args.push(sceneFile);
    if (ajFile) args.push(ajFile);

    console.log('[ViewerManager] Starting viewer with args:', args);

    // Spawn the viewer process
    this.process = spawn(viewerPath, args, {
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: false // We need the window visible
    });

    this.process.stdout.on('data', (data) => {
      console.log('[HSDViewer]', data.toString().trim());
    });

    this.process.stderr.on('data', (data) => {
      console.error('[HSDViewer Error]', data.toString().trim());
    });

    this.process.on('close', (code) => {
      console.log('[ViewerManager] Viewer process exited with code:', code);
      this.cleanup();
    });

    this.process.on('error', (err) => {
      console.error('[ViewerManager] Failed to start viewer:', err);
      this.cleanup();
    });

    // Wait for the viewer to start and connect via named pipe
    await this.connectToPipe();

    return {
      pipeName: this.pipeName,
      hwnd: this.hwnd,
      connected: this.isConnected
    };
  }

  /**
   * Connect to the named pipe
   */
  async connectToPipe() {
    return new Promise((resolve, reject) => {
      const pipePath = `\\\\.\\pipe\\${this.pipeName}`;
      console.log('[ViewerManager] Connecting to pipe:', pipePath);

      let attempts = 0;
      const maxAttempts = 30; // 30 * 500ms = 15 seconds timeout

      const tryConnect = () => {
        attempts++;

        this.pipeClient = net.connect(pipePath, () => {
          console.log('[ViewerManager] Connected to pipe!');
          this.isConnected = true;
          this.setupPipeHandlers();
          resolve();
        });

        this.pipeClient.on('error', (err) => {
          if (attempts < maxAttempts) {
            // Pipe not ready yet, retry
            setTimeout(tryConnect, 500);
          } else {
            reject(new Error(`Failed to connect to viewer pipe after ${maxAttempts} attempts: ${err.message}`));
          }
        });
      };

      // Start trying to connect after a brief delay
      setTimeout(tryConnect, 500);
    });
  }

  /**
   * Set up pipe message handlers
   */
  setupPipeHandlers() {
    this.pipeClient.on('data', (data) => {
      this.messageBuffer += data.toString();

      // Process complete messages (newline-delimited JSON)
      let newlineIndex;
      while ((newlineIndex = this.messageBuffer.indexOf('\n')) !== -1) {
        const line = this.messageBuffer.substring(0, newlineIndex);
        this.messageBuffer = this.messageBuffer.substring(newlineIndex + 1);

        if (line.trim()) {
          try {
            const message = JSON.parse(line);
            this.handleMessage(message);
          } catch (err) {
            console.error('[ViewerManager] Failed to parse message:', line, err);
          }
        }
      }
    });

    this.pipeClient.on('close', () => {
      console.log('[ViewerManager] Pipe closed');
      this.isConnected = false;
    });

    this.pipeClient.on('error', (err) => {
      console.error('[ViewerManager] Pipe error:', err);
    });
  }

  /**
   * Handle incoming message from viewer
   */
  handleMessage(message) {
    console.log('[ViewerManager] Received:', message.type);

    // Store HWND from ready message
    if (message.type === 'ready') {
      this.hwnd = message.hwnd;
      console.log('[ViewerManager] Viewer ready, HWND:', this.hwnd);
    }

    // Notify any registered handlers
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach(handler => handler(message));

    // Also notify 'all' handlers
    const allHandlers = this.messageHandlers.get('all') || [];
    allHandlers.forEach(handler => handler(message));
  }

  /**
   * Register a message handler
   * @param {string} type - Message type to handle, or 'all' for all messages
   * @param {Function} handler - Handler function
   */
  onMessage(type, handler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type).push(handler);
  }

  /**
   * Remove a message handler
   */
  offMessage(type, handler) {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Send a message to the viewer
   * @param {Object} message - Message object to send
   */
  send(message) {
    if (!this.isConnected || !this.pipeClient) {
      console.error('[ViewerManager] Cannot send - not connected');
      return false;
    }

    try {
      const json = JSON.stringify(message) + '\n';
      this.pipeClient.write(json);
      return true;
    } catch (err) {
      console.error('[ViewerManager] Send error:', err);
      return false;
    }
  }

  /**
   * Send camera update
   */
  sendCamera(deltaRotX, deltaRotY, deltaZoom, deltaX, deltaY) {
    return this.send({
      type: 'camera',
      deltaRotX,
      deltaRotY,
      deltaZoom,
      deltaX,
      deltaY
    });
  }

  /**
   * Request animation list
   */
  getAnimList() {
    return this.send({ type: 'getAnimList' });
  }

  /**
   * Load animation by symbol
   */
  loadAnim(symbol) {
    return this.send({ type: 'loadAnim', symbol });
  }

  /**
   * Toggle animation playback
   */
  animToggle() {
    return this.send({ type: 'animToggle' });
  }

  /**
   * Set animation frame
   */
  animSetFrame(frame) {
    return this.send({ type: 'animSetFrame', frame });
  }

  /**
   * Resize/reposition viewer window
   */
  resize(x, y, width, height) {
    return this.send({ type: 'resize', x, y, width, height });
  }

  /**
   * Show viewer window
   */
  show() {
    return this.send({ type: 'show' });
  }

  /**
   * Hide viewer window
   */
  hide() {
    return this.send({ type: 'hide' });
  }

  /**
   * Stop the viewer
   */
  async stop() {
    console.log('[ViewerManager] Stopping viewer...');

    // Send close command
    if (this.isConnected) {
      this.send({ type: 'close' });
    }

    // Close pipe
    if (this.pipeClient) {
      this.pipeClient.destroy();
    }

    // Kill process if still running
    if (this.process && !this.process.killed) {
      this.process.kill();
    }

    this.cleanup();
    console.log('[ViewerManager] Viewer stopped');
  }

  /**
   * Clean up resources
   */
  cleanup() {
    this.process = null;
    this.pipeClient = null;
    this.pipeName = null;
    this.hwnd = null;
    this.isConnected = false;
    this.messageBuffer = '';
  }
}

module.exports = ViewerManager;
