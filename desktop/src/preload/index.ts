import { contextBridge, ipcRenderer, webUtils } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

const api = {
  getApiConfig: (): Promise<{ apiBase: string; apiToken: string }> =>
    ipcRenderer.invoke('get-api-config'),
  openPaperPicker: (): Promise<string | null> =>
    ipcRenderer.invoke('dialog:open-paper'),
  saveMarkdown: (
    payload: { defaultName?: string; content: string }
  ): Promise<{ saved: boolean; path?: string; error?: string }> =>
    ipcRenderer.invoke('dialog:save-markdown', payload),
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
