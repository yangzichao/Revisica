import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

const api = {
  onApiConfig: (
    callback: (config: { apiBase: string; apiToken: string }) => void
  ): void => {
    // Replace any previously-registered listener so HMR reloads or
    // remounting components don't stack duplicate callbacks.
    ipcRenderer.removeAllListeners('api-config')
    ipcRenderer.on('api-config', (_event, config) => callback(config))
  }
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore
  window.electron = electronAPI
  // @ts-ignore
  window.api = api
}
