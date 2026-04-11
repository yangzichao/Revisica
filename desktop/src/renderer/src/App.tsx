import { Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Home from './pages/Home'
import ReviewProgress from './pages/ReviewProgress'
import Results from './pages/Results'

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
    <div className="app">
      <Routes>
        <Route path="/" element={<Home apiBase={apiBase} />} />
        <Route path="/review/:runId" element={<ReviewProgress apiBase={apiBase} />} />
        <Route path="/results/:runId" element={<Results apiBase={apiBase} />} />
      </Routes>
    </div>
  )
}

export default App
