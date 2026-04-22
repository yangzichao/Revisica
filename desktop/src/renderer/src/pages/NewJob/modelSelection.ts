import type { Engine, ModelChoice, ModelRoutes, WizardState } from './types'

const CLAUDE_PROVIDER_PREFIXES = ['claude:', 'claude-cli:', 'anthropic-api:']
const GPT_PROVIDER_PREFIXES = ['codex:', 'codex-cli:', 'openai-api:']

function prefixesForEngine(engine: Engine): string[] {
  return engine === 'claude' ? CLAUDE_PROVIDER_PREFIXES : GPT_PROVIDER_PREFIXES
}

function pickDefaultForEngine(
  options: ModelChoice[] | undefined,
  engine: Engine,
): string | null {
  if (!options) return null
  const prefixes = prefixesForEngine(engine)
  const match = options.find((opt) =>
    prefixes.some((prefix) => opt.value.startsWith(prefix)),
  )
  return match?.value ?? null
}

export interface ResolvedModels {
  writing_model: string | null
  math_model: string | null
}

export function resolveModelsForSubmit(
  state: WizardState,
  modelRoutes: ModelRoutes | null,
): ResolvedModels {
  const effectivelySingle =
    !state.secondaryEnabled || state.secondaryEngine === state.primaryEngine
  if (!effectivelySingle) {
    return { writing_model: null, math_model: null }
  }
  return {
    writing_model: pickDefaultForEngine(modelRoutes?.writing, state.primaryEngine),
    math_model: pickDefaultForEngine(modelRoutes?.math, state.primaryEngine),
  }
}
