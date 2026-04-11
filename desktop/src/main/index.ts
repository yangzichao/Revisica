import { app, shell, BrowserWindow } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { spawn, ChildProcess } from 'child_process'

let pythonProcess: ChildProcess | null = null
const API_PORT = 18321
const API_BASE = `http://127.0.0.1:${API_PORT}`

function getPythonCommand(): { command: string; args: string[] } {
  if (is.dev) {
    // Dev mode: run from source using the project's venv or system Python
    // Look for the venv Python first, fall back to system Python
    const { existsSync } = require('fs')
    const projectRoot = join(__dirname, '..', '..', '..')
    const venvPython = join(projectRoot, '.venv', 'bin', 'python')
    const pythonCommand = existsSync(venvPython) ? venvPython : 'python'
    return {
      command: pythonCommand,
      args: ['-m', 'revisica.api', '--port', String(API_PORT)]
    }
  }
  // Production: use bundled PyInstaller binary
  const resourcePath = join(process.resourcesPath, 'resources', 'python-backend')
  return {
    command: resourcePath,
    args: ['--port', String(API_PORT)]
  }
}

function startPythonBackend(): Promise<void> {
  return new Promise((resolve, reject) => {
    const { command, args } = getPythonCommand()
    console.log(`Starting Python backend: ${command} ${args.join(' ')}`)

    pythonProcess = spawn(command, args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env }
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
  if (pythonProcess) {
    console.log('Stopping Python backend...')
    pythonProcess.kill('SIGTERM')
    // Force kill after 5 seconds
    setTimeout(() => {
      if (pythonProcess) {
        pythonProcess.kill('SIGKILL')
        pythonProcess = null
      }
    }, 5000)
  }
}

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    show: false,
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // Pass API_BASE to renderer
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.send('api-config', { apiBase: API_BASE })
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

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
