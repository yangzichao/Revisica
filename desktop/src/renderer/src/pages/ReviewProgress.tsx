import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

interface TaskStatus {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  detail?: string
}

interface RunStatus {
  run_id: string
  state: 'running' | 'completed' | 'failed'
  tasks: TaskStatus[]
  error?: string
}

export default function ReviewProgress({ apiBase }: { apiBase: string }): JSX.Element {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const [status, setStatus] = useState<RunStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!runId) return

    const poll = setInterval(async () => {
      try {
        const res = await fetch(`${apiBase}/api/status/${runId}`)
        if (!res.ok) {
          setError('Failed to fetch status')
          return
        }
        const data: RunStatus = await res.json()
        setStatus(data)

        if (data.state === 'completed' || data.state === 'failed') {
          clearInterval(poll)
          if (data.state === 'completed') {
            // Navigate to results after a brief pause
            setTimeout(() => navigate(`/results/${runId}`), 1000)
          }
        }
      } catch {
        setError('Lost connection to backend')
      }
    }, 1000)

    return () => clearInterval(poll)
  }, [runId, apiBase, navigate])

  const statusIcon = (s: string): string => {
    switch (s) {
      case 'running':
        return '⟳'
      case 'completed':
        return '✓'
      case 'failed':
        return '✗'
      default:
        return '○'
    }
  }

  return (
    <div className="page review-progress">
      <h1>Review in Progress</h1>
      <p className="muted">Run ID: {runId}</p>

      {error && <div className="banner error">{error}</div>}

      {status && (
        <>
          <div className={`run-state ${status.state}`}>
            {status.state === 'running' ? 'Running...' : status.state}
          </div>

          <div className="task-list">
            {status.tasks.map((task) => (
              <div key={task.name} className={`task-item ${task.status}`}>
                <span className="task-icon">{statusIcon(task.status)}</span>
                <span className="task-name">{task.name}</span>
                {task.detail && <span className="task-detail">{task.detail}</span>}
              </div>
            ))}
          </div>

          {status.state === 'failed' && status.error && (
            <div className="banner error">{status.error}</div>
          )}
        </>
      )}

      <button onClick={() => navigate('/')}>Back to Home</button>
    </div>
  )
}
