export type FileType = 'pdf' | 'tex' | 'md' | null

export type ParserChoice = 'mineru' | 'mathpix' | 'auto' | null

export type BackendMode = 'auto' | 'cli' | 'api' | 'ollama'

export type WizardStep = 1 | 2 | 3

export type ReviewMode = 'polish' | 'review'

export interface WizardState {
  filePath: string
  fileType: FileType
  currentStep: WizardStep
  parserChoice: ParserChoice
  backendMode: BackendMode
  writingModelOverride: string | null
  mathModelOverride: string | null
  mode: ReviewMode
  venueProfile: string
  llmProofReview: boolean
}

export interface ParserInfo {
  name: string
  display_name: string
  available: boolean
  requires: string[]
  handles: string[]
  install_hint: string
}

export type WizardAction =
  | { type: 'SET_FILE'; filePath: string; fileType: FileType }
  | { type: 'CLEAR_FILE' }
  | { type: 'SET_PARSER'; parser: ParserChoice }
  | { type: 'SET_BACKEND_MODE'; mode: BackendMode }
  | { type: 'SET_MODEL_OVERRIDE'; role: 'writing' | 'math'; value: string | null }
  | { type: 'SET_MODE'; mode: ReviewMode }
  | { type: 'SET_VENUE'; venue: string }
  | { type: 'TOGGLE_LLM_PROOF'; value: boolean }
  | { type: 'GO_NEXT' }
  | { type: 'GO_BACK' }
  | { type: 'GO_TO_STEP'; step: WizardStep }

export const DEFAULT_VENUE_PROFILE = 'general-academic'

export const VENUE_PROFILES = [
  'general-academic',
  'econ-general-top',
  'econ-top5',
  'econ-theory',
  'econ-empirical',
  'econ-applied',
] as const
