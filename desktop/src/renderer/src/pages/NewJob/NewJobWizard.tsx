import { useReducer, useEffect, useState, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Bookmark, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'
import { deriveDocumentLabels } from '@/lib/parsedDocuments'
import type { Provider } from '@/components/ProviderCard'
import Stepper from './Stepper'
import Step1ImportFile from './Step1ImportFile'
import Step2ReviewPlan from './Step2ReviewPlan'
import { resolveModelsForSubmit } from './modelSelection'
import {
  DEFAULT_VENUE_PROFILE,
  type Engine,
  type ModelRoutes,
  type ParserChoice,
  type ReviewMode,
  type WizardAction,
  type WizardState,
} from './types'

interface ResumeContext {
  id: string
  title: string
  parserUsed: string
  parsedAt: string
  sourcePath: string
  sectionCount: number
}

type ResumeLoadState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'loaded'; context: ResumeContext }
  | { status: 'error'; message: string }

interface ProviderFetchState {
  providers: Provider[]
  isLoading: boolean
}

const LS_KEYS = {
  parser: 'revisica_new_job_parser',
  mode: 'revisica_new_job_mode',
  venue: 'revisica_new_job_venue',
  llmProof: 'revisica_new_job_llm_proof',
  primaryEngine: 'revisica_new_job_primary_engine',
  secondaryEnabled: 'revisica_new_job_secondary_enabled',
  secondaryEngine: 'revisica_new_job_secondary_engine',
}

function parseEngine(raw: string | null, fallback: Engine): Engine {
  return raw === 'claude' || raw === 'gpt' ? raw : fallback
}

type PersistedFields = Pick<
  WizardState,
  | 'mode'
  | 'venueProfile'
  | 'llmProofReview'
  | 'primaryEngine'
  | 'secondaryEnabled'
  | 'secondaryEngine'
>

function loadPersisted(): PersistedFields {
  // Defaults reproduce the pre-engine-picker behavior: run both families in
  // parallel, with Claude as the nominal primary.
  const defaults: PersistedFields = {
    mode: 'review',
    venueProfile: DEFAULT_VENUE_PROFILE,
    llmProofReview: false,
    primaryEngine: 'claude',
    secondaryEnabled: true,
    secondaryEngine: 'gpt',
  }
  try {
    const mode = (localStorage.getItem(LS_KEYS.mode) as ReviewMode) || 'review'
    const venue = localStorage.getItem(LS_KEYS.venue) || DEFAULT_VENUE_PROFILE
    const llmProof = localStorage.getItem(LS_KEYS.llmProof) === 'true'
    const primaryEngine = parseEngine(
      localStorage.getItem(LS_KEYS.primaryEngine),
      defaults.primaryEngine,
    )
    const secondaryRaw = localStorage.getItem(LS_KEYS.secondaryEnabled)
    const secondaryEnabled =
      secondaryRaw === null ? defaults.secondaryEnabled : secondaryRaw === 'true'
    const secondaryEngine = parseEngine(
      localStorage.getItem(LS_KEYS.secondaryEngine),
      defaults.secondaryEngine,
    )
    return {
      mode: mode === 'polish' ? 'polish' : 'review',
      venueProfile: venue,
      llmProofReview: llmProof,
      primaryEngine,
      secondaryEnabled,
      secondaryEngine,
    }
  } catch {
    return defaults
  }
}

const INITIAL_STATE: WizardState = {
  filePath: '',
  fileType: null,
  currentStep: 1,
  parserChoice: null,
  ...loadPersisted(),
}

function defaultParserFor(
  fileType: WizardState['fileType'],
): ParserChoice {
  if (fileType === 'tex' || fileType === 'md') return 'auto'
  return null
}

function canAdvance(state: WizardState): boolean {
  if (state.currentStep === 1) {
    if (!state.filePath || !state.fileType) return false
    if (state.fileType === 'pdf') {
      return state.parserChoice === 'mineru' || state.parserChoice === 'mathpix'
    }
    return true
  }
  return true
}

function reducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case 'SET_FILE': {
      const nextParser =
        state.fileType === action.fileType
          ? state.parserChoice
          : defaultParserFor(action.fileType)
      return {
        ...state,
        filePath: action.filePath,
        fileType: action.fileType,
        parserChoice: nextParser,
      }
    }
    case 'CLEAR_FILE':
      return {
        ...state,
        filePath: '',
        fileType: null,
        parserChoice: null,
      }
    case 'SET_PARSER':
      return { ...state, parserChoice: action.parser }
    case 'SET_PRIMARY_ENGINE':
      return { ...state, primaryEngine: action.engine }
    case 'SET_SECONDARY_ENABLED':
      return { ...state, secondaryEnabled: action.enabled }
    case 'SET_SECONDARY_ENGINE':
      return { ...state, secondaryEngine: action.engine }
    case 'SET_MODE':
      return { ...state, mode: action.mode }
    case 'SET_VENUE':
      return { ...state, venueProfile: action.venue }
    case 'TOGGLE_LLM_PROOF':
      return { ...state, llmProofReview: action.value }
    case 'GO_NEXT': {
      // UI's NextButton handles validation; here we only clamp bounds.
      if (state.currentStep >= 2) return state
      return {
        ...state,
        currentStep: (state.currentStep + 1) as WizardState['currentStep'],
      }
    }
    case 'GO_BACK': {
      if (state.currentStep <= 1) return state
      return { ...state, currentStep: (state.currentStep - 1) as WizardState['currentStep'] }
    }
    case 'GO_TO_STEP': {
      if (action.step > state.currentStep) return state
      return { ...state, currentStep: action.step }
    }
    default:
      return state
  }
}

export default function NewJobWizard({
  apiBase,
  apiToken,
}: {
  apiBase: string
  apiToken: string
}): JSX.Element {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isBackendReady, setIsBackendReady] = useState(false)
  const [providerFetchState, setProviderFetchState] = useState<ProviderFetchState>({
    providers: [],
    isLoading: true,
  })
  const providers = providerFetchState.providers
  const isLoadingProviders = providerFetchState.isLoading
  const [resumeLoadState, setResumeLoadState] = useState<ResumeLoadState>({ status: 'idle' })
  const [modelRoutes, setModelRoutes] = useState<ModelRoutes | null>(null)

  // Derived values from the discriminated-union resume state — kept as local
  // consts so the rest of the component body stays readable without changes.
  const resumeContext = resumeLoadState.status === 'loaded' ? resumeLoadState.context : null
  const isLoadingResume = resumeLoadState.status === 'loading'
  const resumeError = resumeLoadState.status === 'error' ? resumeLoadState.message : null

  useEffect(() => {
    let cancelled = false
    const load = async (): Promise<void> => {
      try {
        const response = await apiFetch(
          apiBase,
          apiToken,
          '/api/config/model-routes',
        )
        if (!cancelled && response.ok) {
          const data = (await response.json()) as ModelRoutes
          if (!cancelled) setModelRoutes(data)
        }
      } catch {
        // Degrade gracefully — engine still falls back to backend auto-routing
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [apiBase, apiToken])

  const fetchProviders = useCallback(async (): Promise<void> => {
    try {
      const response = await apiFetch(apiBase, apiToken, '/api/providers')
      if (response.ok) {
        const data = await response.json()
        setProviderFetchState({ providers: data.providers || [], isLoading: false })
      } else {
        setProviderFetchState((prev) => ({ ...prev, isLoading: false }))
      }
    } catch {
      // Degrade gracefully — ProviderStatusBadge renders the "not configured" state
      setProviderFetchState((prev) => ({ ...prev, isLoading: false }))
    }
  }, [apiBase, apiToken])

  useEffect(() => {
    fetchProviders()
  }, [fetchProviders])

  useEffect(() => {
    const check = async (): Promise<void> => {
      try {
        const response = await apiFetch(apiBase, apiToken, '/api/health')
        setIsBackendReady(response.ok)
      } catch {
        setIsBackendReady(false)
      }
    }
    check()
    const interval = setInterval(check, 3000)
    return () => clearInterval(interval)
  }, [apiBase, apiToken])

  // When launched as `/?parsed=<id>`, pre-load the saved parse and fast-
  // forward to Step 2 so the user jumps straight to the review plan.
  useEffect(() => {
    const parsedId = searchParams.get('parsed')
    if (!parsedId) {
      setResumeLoadState({ status: 'idle' })
      return
    }
    if (resumeContext && resumeContext.id === parsedId) return
    let cancelled = false
    setResumeLoadState({ status: 'loading' })
    const load = async (): Promise<void> => {
      try {
        const response = await apiFetch(
          apiBase,
          apiToken,
          `/api/parsed-documents/${encodeURIComponent(parsedId)}`,
        )
        if (!response.ok) {
          const data = await response.json().catch(() => ({}))
          throw new Error(data.detail || `Not found (${response.status})`)
        }
        const data = await response.json()
        if (cancelled) return
        setResumeLoadState({
          status: 'loaded',
          context: {
            id: data.id,
            title: data.title || '',
            parserUsed: data.parser_used || 'unknown',
            parsedAt: data.parsed_at || '',
            sourcePath: data.source_path || '',
            sectionCount: data.section_count || 0,
          },
        })
        dispatch({
          type: 'SET_FILE',
          filePath: data.source_path || data.id,
          fileType: 'md',
        })
        dispatch({ type: 'SET_PARSER', parser: 'auto' })
        dispatch({ type: 'GO_TO_STEP', step: 1 })
        dispatch({ type: 'GO_NEXT' })
      } catch (err) {
        if (cancelled) return
        setResumeLoadState({
          status: 'error',
          message: err instanceof Error ? err.message : 'Could not load saved parse',
        })
        setSearchParams({}, { replace: true })
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [searchParams, apiBase, apiToken, resumeContext, setSearchParams])

  const handleExitResume = useCallback((): void => {
    setResumeLoadState({ status: 'idle' })
    setSearchParams({}, { replace: true })
    dispatch({ type: 'CLEAR_FILE' })
    dispatch({ type: 'GO_TO_STEP', step: 1 })
  }, [setSearchParams])

  const handleSubmit = useCallback(async (): Promise<void> => {
    if (!resumeContext && !state.filePath) return
    setIsSubmitting(true)
    setErrorMessage(null)

    try {
      const parserForApi =
        state.fileType === 'pdf' && state.parserChoice
          ? state.parserChoice
          : 'auto'

      const { writing_model, math_model } = resolveModelsForSubmit(
        state,
        modelRoutes,
      )

      const reviewBody: Record<string, unknown> = {
        mode: state.mode,
        venue_profile: state.venueProfile,
        llm_proof_review: state.mode === 'review' && state.llmProofReview,
        writing_model,
        math_model,
      }
      if (resumeContext) {
        reviewBody.parsed_document_id = resumeContext.id
      } else {
        reviewBody.file_path = state.filePath
        reviewBody.parser = parserForApi
      }

      const response = await apiFetch(apiBase, apiToken, '/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reviewBody),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to start review')
      }

      const data = await response.json()

      // Persist common preferences
      try {
        localStorage.setItem(LS_KEYS.mode, state.mode)
        localStorage.setItem(LS_KEYS.venue, state.venueProfile)
        localStorage.setItem(LS_KEYS.llmProof, String(state.llmProofReview))
        localStorage.setItem(LS_KEYS.primaryEngine, state.primaryEngine)
        localStorage.setItem(
          LS_KEYS.secondaryEnabled,
          String(state.secondaryEnabled),
        )
        localStorage.setItem(LS_KEYS.secondaryEngine, state.secondaryEngine)
        if (state.parserChoice) {
          localStorage.setItem(LS_KEYS.parser, state.parserChoice)
        }
      } catch {
        // Private mode or quota — not fatal
      }

      // Append run id to history
      let runIds: string[] = []
      try {
        const stored = localStorage.getItem('revisica_run_ids')
        const parsed = stored ? JSON.parse(stored) : []
        if (Array.isArray(parsed)) {
          runIds = parsed.filter((id): id is string => typeof id === 'string')
        }
      } catch {
        // corrupted — reset
      }
      runIds.unshift(data.run_id)
      localStorage.setItem(
        'revisica_run_ids',
        JSON.stringify(runIds.slice(0, 50)),
      )

      navigate(`/jobs/${data.run_id}`)
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsSubmitting(false)
    }
  }, [state, apiBase, apiToken, navigate, resumeContext, modelRoutes])

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-lg mx-auto px-8 pb-12 pt-6">
        <header className="mb-2">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            New job
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Two steps to kick off a review.
          </p>
        </header>

        <Stepper
          currentStep={state.currentStep}
          onStepClick={(step) => dispatch({ type: 'GO_TO_STEP', step })}
        />

        {!isBackendReady && (
          <div className="card flex items-center gap-3 px-4 py-3 text-sm text-ink-secondary mb-5">
            <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            Connecting to backend...
          </div>
        )}

        {resumeError && (
          <div className="card mb-5 bg-danger/5 border-danger/30 px-4 py-3">
            <div className="text-xs font-semibold text-danger uppercase tracking-wider mb-1">
              Saved parse unavailable
            </div>
            <div className="text-sm text-ink-secondary">{resumeError}</div>
          </div>
        )}

        {state.currentStep === 1 && resumeContext && (
          <ResumeSummaryCard
            context={resumeContext}
            onExit={handleExitResume}
          />
        )}

        {state.currentStep === 1 && !resumeContext && !isLoadingResume && (
          <Step1ImportFile
            apiBase={apiBase}
            apiToken={apiToken}
            state={state}
            dispatch={dispatch}
          />
        )}

        {state.currentStep === 1 && isLoadingResume && !resumeContext && (
          <div className="card flex items-center justify-center gap-2 px-4 py-8 text-sm text-ink-tertiary">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            Loading saved parse…
          </div>
        )}

        {state.currentStep === 2 && (
          <Step2ReviewPlan
            state={state}
            dispatch={dispatch}
            providers={providers}
            isLoadingProviders={isLoadingProviders}
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
            errorMessage={errorMessage}
          />
        )}

        {/* Nav buttons — Step 2 (final) uses its own Start button */}
        {state.currentStep !== 2 && (
          <div className="flex items-center justify-between mt-8">
            <button
              type="button"
              onClick={() => dispatch({ type: 'GO_BACK' })}
              disabled={state.currentStep === 1}
              className={cn(
                'btn-ghost px-3 py-2 text-sm',
                state.currentStep === 1 && 'invisible',
              )}
            >
              <ArrowLeft size={14} />
              Back
            </button>
            <NextButton
              state={state}
              onNext={() => dispatch({ type: 'GO_NEXT' })}
            />
          </div>
        )}
      </div>
    </div>
  )
}

function NextButton({
  state,
  onNext,
}: {
  state: WizardState
  onNext: () => void
}): JSX.Element {
  const disabled = !canAdvance(state)
  const hint = nextBlockedHint(state)
  return (
    <div className="flex items-center gap-3">
      {disabled && hint && (
        <span className="text-xs text-ink-tertiary italic">{hint}</span>
      )}
      <button
        type="button"
        onClick={onNext}
        disabled={disabled}
        className="btn-primary px-5 py-2 text-sm"
      >
        Next
        <ArrowRight size={14} strokeWidth={2.2} />
      </button>
    </div>
  )
}

function nextBlockedHint(state: WizardState): string | null {
  if (state.currentStep === 1) {
    if (!state.filePath) return 'Drop a file to continue'
    if (state.fileType === 'pdf' && !state.parserChoice) {
      return 'Pick a PDF parser'
    }
  }
  return null
}

function ResumeSummaryCard({
  context,
  onExit,
}: {
  context: ResumeContext
  onExit: () => void
}): JSX.Element {
  const { fileName, heading } = deriveDocumentLabels(
    context.sourcePath,
    context.title,
    context.id,
  )
  return (
    <div>
      <header className="mb-4">
        <h2 className="font-serif text-xl font-semibold text-ink tracking-tight">
          Using a saved parse
        </h2>
        <p className="font-serif text-sm text-ink-tertiary italic mt-1">
          No need to re-parse — this document is already ready for review.
        </p>
      </header>

      <div className="card px-5 py-4">
        <div className="flex items-start gap-3">
          <Bookmark
            size={16}
            className="text-success shrink-0 mt-0.5"
            strokeWidth={1.8}
          />
          <div className="flex-1 min-w-0">
            <div className="font-serif text-base font-semibold text-ink leading-snug">
              {heading}
            </div>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <span className="inline-flex items-center px-2 py-0.5 rounded-full border border-accent/30 bg-accent/10 text-accent text-[11px] font-medium">
                parsed via {context.parserUsed}
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full border border-paper-300 bg-paper-50 text-ink-tertiary text-[11px] font-medium">
                {context.sectionCount} section
                {context.sectionCount === 1 ? '' : 's'}
              </span>
              <span className="font-mono text-[11px] text-ink-faint truncate">
                {fileName}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onExit}
            className="btn-ghost px-2 py-1.5 text-xs shrink-0"
            title="Import a different file instead"
          >
            <X size={12} />
            Use a different file
          </button>
        </div>
      </div>
    </div>
  )
}
