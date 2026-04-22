import { Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import Layout from './components/Layout'
import NewJobWizard from './pages/NewJob/NewJobWizard'
import ParsePage from './pages/Parse/ParsePage'
import LibraryPage from './pages/Library/LibraryPage'
import Jobs from './pages/Jobs'
import Integrations from './pages/Integrations'
import IngestionBenchmarkPage from './pages/Benchmarks/IngestionBenchmarkPage'
import Settings from './pages/Settings'
import Help from './pages/Help'

interface ApiConfig {
  apiBase: string
  apiToken: string
}

function App(): JSX.Element {
  const [config, setConfig] = useState<ApiConfig | null>(null)
  const [configError, setConfigError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    if (!window.api?.getApiConfig) {
      setConfigError('Electron bridge unavailable — cannot reach backend.')
      return
    }
    window.api
      .getApiConfig()
      .then((loaded) => {
        if (!cancelled) setConfig(loaded)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setConfigError(
            err instanceof Error ? err.message : 'Failed to load API config.',
          )
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (configError) {
    return (
      <div className="h-full w-full flex items-center justify-center p-8">
        <div className="card max-w-md px-6 py-5 bg-danger/5 border-danger/30">
          <div className="text-xs font-semibold text-danger uppercase tracking-wider mb-1">
            Startup failed
          </div>
          <div className="text-sm text-ink-secondary">{configError}</div>
        </div>
      </div>
    )
  }

  if (!config) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-ink-tertiary font-serif italic">
          <Loader2 size={14} className="animate-spin" />
          Connecting to backend…
        </div>
      </div>
    )
  }

  const { apiBase, apiToken } = config

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<NewJobWizard apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/parse" element={<ParsePage apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/library" element={<LibraryPage apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/jobs" element={<Jobs apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/jobs/:runId" element={<Jobs apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/integrations" element={<Integrations apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/benchmarks/ingestion" element={<IngestionBenchmarkPage apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/settings" element={<Settings apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/help" element={<Help />} />
      </Route>
    </Routes>
  )
}

export default App
