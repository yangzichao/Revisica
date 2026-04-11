import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'

interface ReviewResults {
  run_id: string
  summary: string
  writing_report?: string
  math_report?: string
  run_dir: string
}

export default function Results({ apiBase }: { apiBase: string }): JSX.Element {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const [results, setResults] = useState<ReviewResults | null>(null)
  const [activeTab, setActiveTab] = useState<'summary' | 'writing' | 'math'>('summary')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!runId) return

    const fetchResults = async (): Promise<void> => {
      try {
        const res = await fetch(`${apiBase}/api/results/${runId}`)
        if (!res.ok) {
          setError('Failed to fetch results')
          return
        }
        const data = await res.json()
        setResults(data)
      } catch {
        setError('Lost connection to backend')
      }
    }

    fetchResults()
  }, [runId, apiBase])

  const getActiveContent = (): string => {
    if (!results) return ''
    switch (activeTab) {
      case 'writing':
        return results.writing_report || '*No writing report available*'
      case 'math':
        return results.math_report || '*No math report available*'
      default:
        return results.summary
    }
  }

  return (
    <div className="page results">
      <div className="results-header">
        <h1>Review Results</h1>
        <button onClick={() => navigate('/')}>New Review</button>
      </div>

      {error && <div className="banner error">{error}</div>}

      {results && (
        <>
          <p className="muted">Output: {results.run_dir}</p>

          <div className="tabs">
            <button
              className={activeTab === 'summary' ? 'active' : ''}
              onClick={() => setActiveTab('summary')}
            >
              Summary
            </button>
            <button
              className={activeTab === 'writing' ? 'active' : ''}
              onClick={() => setActiveTab('writing')}
            >
              Writing
            </button>
            <button
              className={activeTab === 'math' ? 'active' : ''}
              onClick={() => setActiveTab('math')}
            >
              Math
            </button>
          </div>

          <div className="report-content">
            <ReactMarkdown>{getActiveContent()}</ReactMarkdown>
          </div>
        </>
      )}
    </div>
  )
}
