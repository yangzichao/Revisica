import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      onApiConfig: (
        callback: (config: { apiBase: string; apiToken: string }) => void
      ) => void
    }
  }
}
