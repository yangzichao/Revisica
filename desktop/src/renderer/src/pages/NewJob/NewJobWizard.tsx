import { useReducer, useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'
import type { Provider } from '@/components/ProviderCard'
import Stepper from './Stepper'
import Step1ImportFile from './Step1ImportFile'
import Step2LlmAccess, { hasAvailableProviderForMode } from './Step2LlmAccess'
import Step3Preferences from './Step3Preferences'
import {
  DEFAULT_VENUE_PROFILE,
  type BackendMode,
  type ParserChoice,
  type ReviewMode,
  type WizardAction,
  type WizardState,
} from './types'

const LS_KEYS = {
  parser: 'revisica_new_job_parser',
  mode: 'revisica_new_job_mode',
  venue: 'revisica_new_job_venue',
  llmProof: 'revisica_new_job_llm_proof',
}

function loadPersisted(): Pick<
  WizardState,
  'mode' | 'venueProfile' | 'llmProofReview'
> {
  try {
    const mode = (localStorage.getItem(LS_KEYS.mode) as ReviewMode) || 'review'
    const venue = localStorage.getItem(LS_KEYS.venue) || DEFAULT_VENUE_PROFILE
    const llmProof = localStorage.getItem(LS_KEYS.llmProof) === 'true'
    return {
      mode: mode === 'polish' ? 'polish' : 'review',
      venueProfile: venue,
      llmProofReview: llmProof,
    }
  } catch {
    return {
      mode: 'review',
      venueProfile: DEFAULT_VENUE_PROFILE,
      llmProofReview: false,
    }
  }
}

const INITIAL_STATE: WizardState = {
  filePath: '',
  fileType: null,
  currentStep: 1,
  parserChoice: null,
  backendMode: 'auto',
  writingModelOverride: null,
  mathModelOverride: null,
  ...loadPersisted(),
}

function defaultParserFor(
  fileType: WizardState['fileType'],
): ParserChoice {
  if (fileType === 'tex' || fileType === 'md') return 'auto'
  return null
}

function canAdvance(state: WizardState, providers: Provider[]): boolean {
  if (state.currentStep === 1) {
    if (!state.filePath || !state.fileType) return false
    if (state.fileType === 'pdf') {
      return state.parserChoice === 'mineru' || state.parserChoice === 'mathpix'
    }
    return true
  }
  if (state.currentStep === 2) {
    if (state.backendMode === 'ollama') return false
    return hasAvailableProviderForMode(providers, state.backendMode)
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
    case 'SET_BACKEND_MODE':
      return { ...state, backendMode: action.mode }
    case 'SET_MODEL_OVERRIDE':
      return action.role === 'writing'
        ? { ...state, writingModelOverride: action.value }
        : { ...state, mathModelOverride: action.value }
    case 'SET_MODE':
      return { ...state, mode: action.mode }
    case 'SET_VENUE':
      return { ...state, venueProfile: action.venue }
    case 'TOGGLE_LLM_PROOF':
      return { ...state, llmProofReview: action.value }
    case 'GO_NEXT': {
      // UI's NextButton handles validation; here we only clamp bounds.
      if (state.currentStep >= 3) return state
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
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isBackendReady, setIsBackendReady] = useState(false)
  const [providers, setProviders] = useState<Provider[]>([])
  const [isLoadingProviders, setIsLoadingProviders] = useState(true)

  const fetchProviders = useCallback(async (): Promise<void> => {
    try {
      const response = await apiFetch(apiBase, apiToken, '/api/providers')
      if (response.ok) {
        const data = await response.json()
        setProviders(data.providers || [])
      }
    } catch {
      // Degrade gracefully — providers remain empty and validation blocks Next
    } finally {
      setIsLoadingProviders(false)
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

  // Load current backend mode from server on mount
  useEffect(() => {
    const load = async (): Promise<void> => {
      try {
        const response = await apiFetch(apiBase, apiToken, '/api/config/backend-mode')
        if (response.ok) {
          const data = await response.json()
          const mode = data.backend_mode as BackendMode
          if (mode === 'auto' || mode === 'cli' || mode === 'api') {
            dispatch({ type: 'SET_BACKEND_MODE', mode })
          }
        }
      } catch {
        // leave default
      }
    }
    load()
  }, [apiBase, apiToken])

  const handleSubmit = useCallback(async (): Promise<void> => {
    if (!state.filePath) return
    setIsSubmitting(true)
    setErrorMessage(null)

    try {
      const parserForApi =
        state.fileType === 'pdf' && state.parserChoice
          ? state.parserChoice
          : 'auto'

      const response = await apiFetch(apiBase, apiToken, '/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: state.filePath,
          mode: state.mode,
          venue_profile: state.venueProfile,
          llm_proof_review: state.mode === 'review' && state.llmProofReview,
          parser: parserForApi,
          writing_model: state.writingModelOverride,
          math_model: state.mathModelOverride,
        }),
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
  }, [state, apiBase, apiToken, navigate])

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-lg mx-auto px-8 pb-12 pt-6">
        <header className="mb-2">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            New job
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Three steps to kick off a review.
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

        {state.currentStep === 1 && (
          <Step1ImportFile
            apiBase={apiBase}
            apiToken={apiToken}
            state={state}
            dispatch={dispatch}
          />
        )}
        {state.currentStep === 2 && (
          <Step2LlmAccess
            apiBase={apiBase}
            apiToken={apiToken}
            state={state}
            dispatch={dispatch}
            providers={providers}
            isLoadingProviders={isLoadingProviders}
            onProvidersRefresh={fetchProviders}
          />
        )}
        {state.currentStep === 3 && (
          <Step3Preferences
            apiBase={apiBase}
            apiToken={apiToken}
            state={state}
            dispatch={dispatch}
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
            errorMessage={errorMessage}
          />
        )}

        {/* Nav buttons — Step 3 uses its own Start button */}
        {state.currentStep !== 3 && (
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
              providers={providers}
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
  providers,
  onNext,
}: {
  state: WizardState
  providers: Provider[]
  onNext: () => void
}): JSX.Element {
  const disabled = !canAdvance(state, providers)
  const hint = nextBlockedHint(state, providers)
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

function nextBlockedHint(state: WizardState, providers: Provider[]): string | null {
  if (state.currentStep === 1) {
    if (!state.filePath) return 'Drop a file to continue'
    if (state.fileType === 'pdf' && !state.parserChoice) {
      return 'Pick a PDF parser'
    }
    return null
  }
  if (state.currentStep === 2) {
    if (state.backendMode === 'ollama') {
      return 'Ollama is preview-only — choose another tab'
    }
    if (!hasAvailableProviderForMode(providers, state.backendMode)) {
      if (state.backendMode === 'api') return 'Save an API key to continue'
      if (state.backendMode === 'cli') return 'No CLI provider available'
      return 'No provider available'
    }
  }
  return null
}
