import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      getApiConfig: () => Promise<{ apiBase: string; apiToken: string }>
      openPaperPicker: () => Promise<string | null>
      saveMarkdown: (payload: {
        defaultName?: string
        content: string
      }) => Promise<{ saved: boolean; path?: string; error?: string }>
      getPathForFile: (file: File) => string
    }
  }
}
