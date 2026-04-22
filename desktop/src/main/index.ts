import { app, shell, BrowserWindow, dialog, ipcMain } from 'electron'
import { join } from 'path'
import { randomBytes } from 'crypto'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { spawn, ChildProcess } from 'child_process'
import { TRAFFIC_LIGHT_POSITION } from '../shared/window-chrome'

let pythonProcess: ChildProcess | null = null
const API_PORT = 18321
const API_BASE = `http://127.0.0.1:${API_PORT}`
// Minted per launch; shared with the Python backend via env var and with the
// renderer via IPC. No external caller ever sees it.
const API_TOKEN = randomBytes(32).toString('base64url')

function getPythonCommand(): { command: string; args: string[] } {
  if (is.dev) {
    // Dev mode: run from source
    // Try venv Python first, then pyenv python3, then system python
    const { existsSync } = require('fs')
    const { execSync } = require('child_process')
    const projectRoot = join(__dirname, '..', '..', '..')

    let pythonCommand = 'python3'
    const venvPython = join(projectRoot, '.venv', 'bin', 'python3')
    if (existsSync(venvPython)) {
      // Check if venv Python is new enough (3.10+)
      try {
        const version = execSync(`${venvPython} -c "import sys; print(sys.version_info.minor)"`)
          .toString()
          .trim()
        if (parseInt(version) >= 10) {
          pythonCommand = venvPython
        }
      } catch {
        // Fall through to system Python
      }
    }

    return {
      command: pythonCommand,
      args: ['-m', 'revisica.api', '--port', String(API_PORT)]
    }
  }
  // Production: use the bundled PyInstaller --onedir output. The executable
  // lives *inside* the directory; pointing Electron at the directory itself
  // would spawn /bin/sh and fail silently.
  const backendExecutable = join(
    process.resourcesPath,
    'resources',
    'python-backend',
    'python-backend'
  )
  return {
    command: backendExecutable,
    args: ['--port', String(API_PORT)]
  }
}

function startPythonBackend(): Promise<void> {
  return new Promise((resolve, reject) => {
    const { command, args } = getPythonCommand()
    console.log(`Starting Python backend: ${command} ${args.join(' ')}`)

    // In dev mode, run from project root so 'pip install -e .' works
    const projectRoot = is.dev
      ? join(__dirname, '..', '..', '..')
      : process.resourcesPath

    pythonProcess = spawn(command, args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: projectRoot,
      env: { ...process.env, REVISICA_API_TOKEN: API_TOKEN }
    })

    pythonProcess.stdout?.on('data', (data) => {
      console.log(`[python] ${data}`)
    })

    pythonProcess.stderr?.on('data', (data) => {
      console.error(`[python] ${data}`)
    })

    pythonProcess.on('error', (err) => {
      console.error('Failed to start Python backend:', err)
      reject(err)
    })

    pythonProcess.on('exit', (code) => {
      console.log(`Python backend exited with code ${code}`)
      pythonProcess = null
    })

    // Poll for readiness
    const maxAttempts = 30
    let attempts = 0
    const poll = setInterval(async () => {
      attempts++
      try {
        const response = await fetch(`${API_BASE}/api/health`)
        if (response.ok) {
          clearInterval(poll)
          console.log('Python backend is ready')
          resolve()
        }
      } catch {
        if (attempts >= maxAttempts) {
          clearInterval(poll)
          reject(new Error('Python backend failed to start within 30 seconds'))
        }
      }
    }, 1000)
  })
}

function stopPythonBackend(): void {
  if (!pythonProcess) return
  console.log('Stopping Python backend...')
  const target = pythonProcess
  const targetPid = target.pid
  target.kill('SIGTERM')
  setTimeout(() => {
    // Only force-kill if the same process is still running — avoids
    // SIGKILL'ing a freshly-spawned successor with a recycled slot.
    if (pythonProcess && pythonProcess.pid === targetPid) {
      pythonProcess.kill('SIGKILL')
      pythonProcess = null
    }
  }, 5000)
}

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    show: false,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { ...TRAFFIC_LIGHT_POSITION },
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    try {
      const { protocol } = new URL(details.url)
      if (protocol === 'http:' || protocol === 'https:') {
        shell.openExternal(details.url)
      }
    } catch {
      // Ignore malformed URLs
    }
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// Renderer pulls config on mount instead of main pushing on did-finish-load,
// which raced with React's effect registration and left apiToken = '' → 401.
ipcMain.handle('get-api-config', () => ({ apiBase: API_BASE, apiToken: API_TOKEN }))

ipcMain.handle('dialog:open-paper', async (event) => {
  const window = BrowserWindow.fromWebContents(event.sender)
  if (!window) return null
  const result = await dialog.showOpenDialog(window, {
    title: 'Choose a paper',
    properties: ['openFile'],
    filters: [
      { name: 'Papers', extensions: ['pdf', 'tex', 'md', 'mmd', 'markdown'] },
      { name: 'PDF', extensions: ['pdf'] },
      { name: 'LaTeX', extensions: ['tex'] },
      { name: 'Markdown', extensions: ['md', 'mmd', 'markdown'] }
    ]
  })
  if (result.canceled || result.filePaths.length === 0) return null
  return result.filePaths[0]
})

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.revisica.app')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  try {
    await startPythonBackend()
  } catch (err) {
    console.error('Failed to start Python backend:', err)
    // Still open the window — it will show a connection error in the UI
  }

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  stopPythonBackend()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('will-quit', () => {
  stopPythonBackend()
})
