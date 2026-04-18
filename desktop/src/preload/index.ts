import { contextBridge, ipcRenderer, webUtils } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

const api = {
  onApiConfig: (
    callback: (config: { apiBase: string; apiToken: string }) => void
  ): void => {
    // Replace any previously-registered listener so HMR reloads or
    // remounting components don't stack duplicate callbacks.
    ipcRenderer.removeAllListeners('api-config')
    ipcRenderer.on('api-config', (_event, config) => callback(config))
  },
  openPaperPicker: (): Promise<string | null> =>
    ipcRenderer.invoke('dialog:open-paper'),
  // Electron 32+ removed File.path on dropped files; webUtils is the
  // replacement. Returns '' for non-local sources (iCloud cloud-only,
  // web drags, sandboxed attachments).
  getPathForFile: (file: File): string => webUtils.getPathForFile(file)
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
