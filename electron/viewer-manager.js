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
    // Track process state for fail-fast during pipe connection
    this._processExited = false;
    this._stderrChunks = [];
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
      // Production: use the self-contained publish in resources
      return path.join(
        process.resourcesPath,
        'utility', 'HSDRawViewer',
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

    // Reset state
    this._processExited = false;
    this._stderrChunks = [];

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
      const text = data.toString().trim();
      console.error('[HSDViewer Error]', text);
      this._stderrChunks.push(text);
    });

    this.process.on('close', (code) => {
      console.log('[ViewerManager] Viewer process exited with code:', code);
      this._processExited = true;
      this.cleanup();
    });

    this.process.on('error', (err) => {
      console.error('[ViewerManager] Failed to start viewer:', err);
      this._processExited = true;
      this._stderrChunks.push(err.message);
      this.cleanup();
    });

    // Wait for PIPE_READY signal from stdout, then connect
    await this.waitForPipeReady();
    await this.connectToPipe();

    return {
      pipeName: this.pipeName,
      hwnd: this.hwnd,
      connected: this.isConnected
    };
  }

  /**
   * Wait for the C# viewer to signal that it's created the named pipe.
   * Fails fast if the process exits before signaling.
   */
  waitForPipeReady() {
    return new Promise((resolve, reject) => {
      let resolved = false;

      const timeout = setTimeout(() => {
        if (!resolved) {
          resolved = true;
          const stderr = this._stderrChunks.join('\n').trim();
          reject(new Error(
            `HSDRawViewer did not become ready within 30 seconds` +
            (stderr ? `\n\nViewer output:\n${stderr}` : '')
          ));
        }
      }, 30000);

      // Listen for PIPE_READY on stdout
      const onData = (data) => {
        if (resolved) return;
        const text = data.toString();
        if (text.includes('PIPE_READY')) {
          resolved = true;
          clearTimeout(timeout);
          // Remove this specific listener (keep the logging one)
          this.process?.stdout?.removeListener('data', onData);
          resolve();
        }
      };
      this.process.stdout.on('data', onData);

      // Fail fast if process exits before signaling
      const onClose = (code) => {
        if (!resolved) {
          resolved = true;
          clearTimeout(timeout);
          const stderr = this._stderrChunks.join('\n').trim();
          reject(new Error(
            `HSDRawViewer crashed during startup (exit code ${code})` +
            (stderr ? `\n\nViewer output:\n${stderr}` : '')
          ));
        }
      };
      this.process.on('close', onClose);

      const onError = (err) => {
        if (!resolved) {
          resolved = true;
          clearTimeout(timeout);
          reject(new Error(`HSDRawViewer failed to launch: ${err.message}`));
        }
      };
      this.process.on('error', onError);
    });
  }

  /**
   * Connect to the named pipe (called only after PIPE_READY)
   */
  async connectToPipe() {
    return new Promise((resolve, reject) => {
      const pipePath = `\\\\.\\pipe\\${this.pipeName}`;
      console.log('[ViewerManager] Connecting to pipe:', pipePath);

      let attempts = 0;
      const maxAttempts = 10; // Only need a few retries since we know the pipe exists
      let settled = false;

      const tryConnect = () => {
        if (settled) return;

        // Fail fast if process died
        if (this._processExited) {
          settled = true;
          const stderr = this._stderrChunks.join('\n').trim();
          reject(new Error(
            'HSDRawViewer process exited before pipe connection could be established' +
            (stderr ? `\n\nViewer output:\n${stderr}` : '')
          ));
          return;
        }

        attempts++;
        this.pipeClient = net.connect(pipePath, () => {
          if (!settled) {
            settled = true;
            console.log('[ViewerManager] Connected to pipe!');
            this.isConnected = true;
            this.setupPipeHandlers();
            resolve();
          }
        });

        this.pipeClient.on('error', (err) => {
          if (settled) return;
          if (attempts < maxAttempts) {
            setTimeout(tryConnect, 200);
          } else {
            settled = true;
            const stderr = this._stderrChunks.join('\n').trim();
            reject(new Error(
              `Failed to connect to viewer pipe after ${maxAttempts} attempts: ${err.message}` +
              (stderr ? `\n\nViewer output:\n${stderr}` : '')
            ));
          }
        });
      };

      tryConnect();
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
   * Set CSP mode (enables special camera for character select portraits)
   */
  setCspMode(enabled) {
    return this.send({ type: 'setCspMode', enabled });
  }

  /**
   * Set grid visibility
   */
  setGrid(enabled) {
    return this.send({ type: 'setGrid', enabled });
  }

  /**
   * Set background visibility
   */
  setBackground(enabled) {
    return this.send({ type: 'setBackground', enabled });
  }

  /**
   * Export current scene settings (camera, frame, animation)
   * Returns promise that resolves with scene data
   */
  exportScene() {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.offMessage('sceneExported', handler);
        reject(new Error('Scene export timed out'));
      }, 5000);

      const handler = (message) => {
        clearTimeout(timeout);
        this.offMessage('sceneExported', handler);
        if (message.success) {
          resolve(message.scene);
        } else {
          reject(new Error(message.error || 'Scene export failed'));
        }
      };

      this.onMessage('sceneExported', handler);
      this.send({ type: 'exportScene' });
    });
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
