import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      getApiConfig: () => Promise<{ apiBase: string; apiToken: string }>
      openPaperPicker: () => Promise<string | null>
      getPathForFile: (file: File) => string
    }
  }
}
