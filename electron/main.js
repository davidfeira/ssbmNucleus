const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

let pythonProcess = null;
let mainWindow = null;

// Determine if we're in development or production
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

function getResourcePath(relativePath) {
  if (isDev) {
    // In development, paths are relative to project root
    return path.join(__dirname, '..', relativePath);
  } else {
    // In production, use app resources
    return path.join(process.resourcesPath, relativePath);
  }
}

function startFlaskServer() {
  const backendPath = getResourcePath('backend/mex_api.py');

  console.log('[Electron] Starting Flask backend...');
  console.log('[Electron] Backend path:', backendPath);

  if (!fs.existsSync(backendPath)) {
    console.error('[Electron] Backend file not found:', backendPath);
    return;
  }

  pythonProcess = spawn('python', [backendPath], {
    cwd: path.dirname(backendPath),
    stdio: ['ignore', 'pipe', 'pipe']
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Flask] ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Flask Error] ${data.toString().trim()}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`[Flask] Process exited with code ${code}`);
    pythonProcess = null;
  });

  pythonProcess.on('error', (err) => {
    console.error('[Flask] Failed to start:', err);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    backgroundColor: '#1a1a1a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      enableRemoteModule: false
    },
    icon: path.join(__dirname, '../viewer/public/favicon.ico')
  });

  // Load the app
  if (isDev) {
    // In development, load from Vite dev server
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load built files
    const indexPath = path.join(__dirname, '../viewer/dist/index.html');
    mainWindow.loadFile(indexPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers for file dialogs
ipcMain.handle('open-project-dialog', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'MEX Project', extensions: ['mexproj'] }
    ],
    title: 'Open MEX Project'
  });

  if (result.canceled || result.filePaths.length === 0) {
    return null;
  }

  return result.filePaths[0];
});

ipcMain.handle('open-iso-dialog', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'GameCube ISO', extensions: ['iso', 'gcm'] },
      { name: 'All Files', extensions: ['*'] }
    ],
    title: 'Select Vanilla Melee ISO (v1.02)'
  });

  if (result.canceled || result.filePaths.length === 0) {
    return null;
  }

  return result.filePaths[0];
});

ipcMain.handle('select-directory-dialog', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory', 'createDirectory'],
    title: 'Select Project Output Directory'
  });

  if (result.canceled || result.filePaths.length === 0) {
    return null;
  }

  return result.filePaths[0];
});

// App lifecycle
app.whenReady().then(() => {
  console.log('[Electron] App ready');

  // Start Flask backend
  startFlaskServer();

  // Wait a bit for Flask to start, then create window
  setTimeout(() => {
    createWindow();
  }, 2000);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // On macOS, keep app running unless explicitly quit
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  console.log('[Electron] Shutting down...');

  // Kill Flask backend
  if (pythonProcess) {
    console.log('[Electron] Killing Flask process...');
    pythonProcess.kill();
    pythonProcess = null;
  }
});

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error('[Electron] Uncaught exception:', error);
});
