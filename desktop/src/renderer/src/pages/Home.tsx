import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

const VENUE_PROFILES = [
  'general-academic',
  'econ-general-top',
  'econ-top5',
  'econ-theory',
  'econ-empirical',
  'econ-applied'
]

interface Provider {
  name: string
  display_name: string
  model_family: string
  available: boolean
}

export default function Home({ apiBase }: { apiBase: string }): JSX.Element {
  const navigate = useNavigate()
  const [filePath, setFilePath] = useState('')
  const [mode, setMode] = useState<'review' | 'polish'>('review')
  const [venueProfile, setVenueProfile] = useState('general-academic')
  const [llmProofReview, setLlmProofReview] = useState(false)
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [backendReady, setBackendReady] = useState(false)

  useEffect(() => {
    const checkHealth = async (): Promise<void> => {
      try {
        const res = await fetch(`${apiBase}/api/health`)
        if (res.ok) {
          setBackendReady(true)
          const provRes = await fetch(`${apiBase}/api/providers`)
          if (provRes.ok) {
            const data = await provRes.json()
            setProviders(data.providers)
          }
        }
      } catch {
        setBackendReady(false)
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 3000)
    return () => clearInterval(interval)
  }, [apiBase])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) {
      setFilePath((file as File & { path?: string }).path || file.name)
    }
  }, [])

  const handleSubmit = async (): Promise<void> => {
    if (!filePath) return
    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`${apiBase}/api/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: filePath,
          mode,
          venue_profile: venueProfile,
          llm_proof_review: mode === 'review' && llmProofReview
        })
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to start review')
      }

      const data = await res.json()
      navigate(`/review/${data.run_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const availableCount = providers.filter((p) => p.available).length

  return (
    <div className="page home">
      <h1>Revisica</h1>
      <p className="subtitle">Academic paper revision agent</p>

      {!backendReady && (
        <div className="banner warning">Connecting to backend...</div>
      )}

      <div
        className="drop-zone"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <p>Drag & drop a paper here</p>
        <p className="muted">.tex or .pdf</p>
      </div>

      <div className="form-group">
        <label htmlFor="file-path">File path</label>
        <input
          id="file-path"
          type="text"
          value={filePath}
          onChange={(e) => setFilePath(e.target.value)}
          placeholder="/path/to/paper.tex or paper.pdf"
        />
      </div>

      <div className="form-group">
        <label htmlFor="mode">Review mode</label>
        <div className="mode-selector">
          <button
            className={mode === 'polish' ? 'active' : ''}
            onClick={() => setMode('polish')}
          >
            Polish
            <span className="mode-desc">Writing style only</span>
          </button>
          <button
            className={mode === 'review' ? 'active' : ''}
            onClick={() => setMode('review')}
          >
            Review
            <span className="mode-desc">Full deep analysis</span>
          </button>
        </div>
      </div>

      {mode === 'review' && (
        <>
          <div className="form-group">
            <label htmlFor="venue-profile">Venue profile</label>
            <select
              id="venue-profile"
              value={venueProfile}
              onChange={(e) => setVenueProfile(e.target.value)}
            >
              {VENUE_PROFILES.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>

          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={llmProofReview}
                onChange={(e) => setLlmProofReview(e.target.checked)}
              />
              Enable LLM proof review (deeper math analysis)
            </label>
          </div>
        </>
      )}

      <div className="providers">
        <h3>Providers ({availableCount} available)</h3>
        {providers.length === 0 ? (
          <p className="muted">Checking providers...</p>
        ) : (
          providers.map((p) => (
            <span
              key={p.name}
              className={`provider-badge ${p.available ? 'available' : 'missing'}`}
            >
              {p.display_name}: {p.available ? 'ready' : 'not configured'}
            </span>
          ))
        )}
      </div>

      {error && <div className="banner error">{error}</div>}

      <button
        className="primary"
        onClick={handleSubmit}
        disabled={!filePath || !backendReady || loading || availableCount === 0}
      >
        {loading ? 'Starting...' : mode === 'polish' ? 'Start Polish' : 'Start Review'}
      </button>
    </div>
  )
}
