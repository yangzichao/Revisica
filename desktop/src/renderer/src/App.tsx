import { Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import NewJobWizard from './pages/NewJob/NewJobWizard'
import Jobs from './pages/Jobs'
import Providers from './pages/Providers'
import Settings from './pages/Settings'
import Help from './pages/Help'
import Parse from './pages/Parse'

const DEFAULT_API_BASE = 'http://127.0.0.1:18321'

function App(): JSX.Element {
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE)
  const [apiToken, setApiToken] = useState('')

  useEffect(() => {
    if (window.api?.onApiConfig) {
      window.api.onApiConfig((config) => {
        setApiBase(config.apiBase)
        setApiToken(config.apiToken)
      })
    }
  }, [])

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<NewJobWizard apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/jobs" element={<Jobs apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/jobs/:runId" element={<Jobs apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/providers" element={<Providers apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/parse" element={<Parse apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/settings" element={<Settings apiBase={apiBase} apiToken={apiToken} />} />
        <Route path="/help" element={<Help />} />
      </Route>
    </Routes>
  )
}

export default App
