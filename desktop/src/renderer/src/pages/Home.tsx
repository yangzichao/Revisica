import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileUp, FileCheck, ArrowRight, Sparkles, BookOpen } from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'

const VENUE_PROFILES = [
  'general-academic',
  'econ-general-top',
  'econ-top5',
  'econ-theory',
  'econ-empirical',
  'econ-applied',
]

export default function Home({
  apiBase,
  apiToken,
}: {
  apiBase: string
  apiToken: string
}): JSX.Element {
  const navigate = useNavigate()

  const [filePath, setFilePath] = useState('')
  const [mode, setMode] = useState<'review' | 'polish'>('review')
  const [venueProfile, setVenueProfile] = useState('general-academic')
  const [llmProofReview, setLlmProofReview] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isBackendReady, setIsBackendReady] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)

  useEffect(() => {
    const checkHealth = async (): Promise<void> => {
      try {
        const response = await apiFetch(apiBase, apiToken, '/api/health')
        setIsBackendReady(response.ok)
      } catch {
        setIsBackendReady(false)
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 3000)
    return () => clearInterval(interval)
  }, [apiBase, apiToken])

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(false)
    const file = event.dataTransfer.files[0]
    if (file) {
      const electronFile = file as File & { path?: string }
      setFilePath(electronFile.path || file.name)
    }
  }, [])

  const handleSubmit = async (): Promise<void> => {
    if (!filePath) return
    setIsSubmitting(true)
    setErrorMessage(null)

    try {
      const response = await apiFetch(apiBase, apiToken, '/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: filePath,
          mode,
          venue_profile: venueProfile,
          llm_proof_review: mode === 'review' && llmProofReview,
        }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to start review')
      }

      const data = await response.json()
      const storedIds = localStorage.getItem('revisica_run_ids')
      const runIds: string[] = storedIds ? JSON.parse(storedIds) : []
      runIds.unshift(data.run_id)
      localStorage.setItem('revisica_run_ids', JSON.stringify(runIds.slice(0, 50)))
      navigate(`/jobs/${data.run_id}`)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unknown error')
    } finally {
      setIsSubmitting(false)
    }
  }

  const canSubmit = filePath.trim().length > 0 && isBackendReady && !isSubmitting

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-lg mx-auto px-8 py-12">
        <header className="mb-10">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            New Review
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Drop your paper, choose a mode, and let Revisica do the rest.
          </p>
        </header>

        {!isBackendReady && (
          <div className="card flex items-center gap-3 px-4 py-3 text-sm text-ink-secondary mb-6">
            <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            Connecting to backend...
          </div>
        )}

        {/* File drop zone */}
        <div
          className={cn(
            'rounded-xl border-2 border-dashed px-6 py-10 text-center',
            'transition-colors duration-200 cursor-pointer mb-3',
            isDragOver
              ? 'border-accent bg-accent/5'
              : filePath
                ? 'border-success/40 bg-success/[0.03]'
                : 'border-paper-300 hover:border-paper-400',
          )}
          onDrop={handleDrop}
          onDragOver={(event) => {
            event.preventDefault()
            setIsDragOver(true)
          }}
          onDragLeave={() => setIsDragOver(false)}
        >
          {filePath ? (
            <div className="flex items-center justify-center gap-3">
              <FileCheck size={20} className="text-success" strokeWidth={1.7} />
              <span className="font-mono text-sm text-ink truncate max-w-xs">
                {filePath.split('/').pop()}
              </span>
              <button
                onClick={(event) => {
                  event.stopPropagation()
                  setFilePath('')
                }}
                className="text-xs text-ink-tertiary hover:text-accent underline underline-offset-2 bg-transparent border-none cursor-pointer"
              >
                change
              </button>
            </div>
          ) : (
            <>
              <FileUp size={28} className="mx-auto mb-2 text-ink-faint" strokeWidth={1.3} />
              <p className="text-sm text-ink-secondary font-medium">Drop a paper here</p>
              <p className="text-xs text-ink-faint mt-1">.tex or .pdf</p>
            </>
          )}
        </div>

        <input
          type="text"
          value={filePath}
          onChange={(event) => setFilePath(event.target.value)}
          placeholder="Or type a file path..."
          className="input font-mono mb-8"
        />

        {/* Mode selector */}
        <fieldset className="mb-8">
          <legend className="text-xs font-semibold text-ink-tertiary uppercase tracking-wider mb-3">
            Mode
          </legend>
          <div className="grid grid-cols-2 gap-3">
            <ModeCard
              icon={Sparkles}
              title="Polish"
              description="Writing style only"
              isSelected={mode === 'polish'}
              onClick={() => setMode('polish')}
            />
            <ModeCard
              icon={BookOpen}
              title="Review"
              description="Full deep analysis"
              isSelected={mode === 'review'}
              onClick={() => setMode('review')}
            />
          </div>
        </fieldset>

        {/* Review-specific options */}
        {mode === 'review' && (
          <div className="mb-8 space-y-5">
            <div>
              <label className="block text-xs font-semibold text-ink-tertiary uppercase tracking-wider mb-2">
                Venue profile
              </label>
              <select
                value={venueProfile}
                onChange={(event) => setVenueProfile(event.target.value)}
                className="input"
              >
                {VENUE_PROFILES.map((profile) => (
                  <option key={profile} value={profile}>
                    {profile}
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-3 cursor-pointer text-sm text-ink-secondary hover:text-ink transition-colors">
              <input
                type="checkbox"
                checked={llmProofReview}
                onChange={(event) => setLlmProofReview(event.target.checked)}
                className="w-4 h-4 rounded border-paper-400 accent-accent"
              />
              LLM proof review
              <span className="text-xs text-ink-faint">— deeper math analysis</span>
            </label>
          </div>
        )}

        {/* Error message */}
        {errorMessage && (
          <div className="rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger mb-6">
            {errorMessage}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="btn-primary w-full py-3"
        >
          {isSubmitting ? (
            'Starting...'
          ) : (
            <>
              {mode === 'polish' ? 'Start Polish' : 'Start Review'}
              <ArrowRight size={16} strokeWidth={2.2} />
            </>
          )}
        </button>
      </div>
    </div>
  )
}

function ModeCard({
  icon: Icon,
  title,
  description,
  isSelected,
  onClick,
}: {
  icon: typeof Sparkles
  title: string
  description: string
  isSelected: boolean
  onClick: () => void
}): JSX.Element {
  return (
    <button
      onClick={onClick}
      className={cn(
        'card flex items-center gap-3 px-4 py-4 text-left',
        'transition-all duration-150 cursor-pointer',
        isSelected && 'border-accent/40 ring-2 ring-accent/15',
      )}
    >
      <Icon
        size={20}
        strokeWidth={1.5}
        className={isSelected ? 'text-accent' : 'text-ink-faint'}
      />
      <div>
        <div className={cn('text-sm font-semibold', isSelected ? 'text-accent' : 'text-ink')}>
          {title}
        </div>
        <div className="text-xs text-ink-tertiary mt-0.5">{description}</div>
      </div>
    </button>
  )
}
