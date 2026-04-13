import { Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import Home from './pages/Home'
import Jobs from './pages/Jobs'
import Providers from './pages/Providers'
import Settings from './pages/Settings'
import Help from './pages/Help'
import Parse from './pages/Parse'

const DEFAULT_API_BASE = 'http://127.0.0.1:18321'

function App(): JSX.Element {
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE)

  useEffect(() => {
    if (window.api?.onApiConfig) {
      window.api.onApiConfig((config) => {
        setApiBase(config.apiBase)
      })
    }
  }, [])

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home apiBase={apiBase} />} />
        <Route path="/jobs" element={<Jobs apiBase={apiBase} />} />
        <Route path="/jobs/:runId" element={<Jobs apiBase={apiBase} />} />
        <Route path="/providers" element={<Providers apiBase={apiBase} />} />
        <Route path="/parse" element={<Parse apiBase={apiBase} />} />
        <Route path="/settings" element={<Settings apiBase={apiBase} />} />
        <Route path="/help" element={<Help />} />
      </Route>
    </Routes>
  )
}

export default App
