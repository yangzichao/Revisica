import { cn } from '@/lib/utils'
import type { Engine, ModelChoice } from './types'

const CLAUDE_PROVIDER_PREFIXES = ['claude:', 'claude-cli:', 'anthropic-api:']
const GPT_PROVIDER_PREFIXES = ['codex:', 'codex-cli:', 'openai-api:']

function prefixesForEngine(engine: Engine): string[] {
  return engine === 'claude' ? CLAUDE_PROVIDER_PREFIXES : GPT_PROVIDER_PREFIXES
}

export function pickDefaultForEngine(
  options: ModelChoice[] | undefined,
  engine: Engine,
): string | null {
  if (!options) return null
  const prefixes = prefixesForEngine(engine)
  const match = options.find((opt) => prefixes.some((p) => opt.value.startsWith(p)))
  return match?.value ?? null
}

interface EngineOption {
  key: Engine
  label: string
}

const ENGINE_OPTIONS: EngineOption[] = [
  { key: 'claude', label: 'Claude' },
  { key: 'gpt', label: 'GPT' },
]

interface EnginePickerProps {
  primaryEngine: Engine
  secondaryEnabled: boolean
  secondaryEngine: Engine
  onPrimaryChange: (engine: Engine) => void
  onSecondaryEnabledChange: (enabled: boolean) => void
  onSecondaryChange: (engine: Engine) => void
}

export default function EnginePicker({
  primaryEngine,
  secondaryEnabled,
  secondaryEngine,
  onPrimaryChange,
  onSecondaryEnabledChange,
  onSecondaryChange,
}: EnginePickerProps): JSX.Element {
  const effectivelySingle =
    !secondaryEnabled || secondaryEngine === primaryEngine

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs font-semibold text-ink-tertiary uppercase tracking-wider mb-2">
          Primary engine
        </label>
        <SegmentedRow
          options={ENGINE_OPTIONS}
          value={primaryEngine}
          onChange={onPrimaryChange}
        />
      </div>

      <div>
        <label className="flex items-center gap-3 cursor-pointer text-sm text-ink-secondary hover:text-ink transition-colors">
          <input
            type="checkbox"
            checked={secondaryEnabled}
            onChange={(e) => onSecondaryEnabledChange(e.target.checked)}
            className="w-4 h-4 rounded border-paper-400 accent-accent"
          />
          Add a secondary engine
          <span className="text-xs text-ink-faint">— runs a cross-check</span>
        </label>

        {secondaryEnabled && (
          <div className="mt-2 pl-7">
            <SegmentedRow
              options={ENGINE_OPTIONS}
              value={secondaryEngine}
              onChange={onSecondaryChange}
            />
          </div>
        )}
      </div>

      <div className="text-[11px] text-ink-faint italic">
        {effectivelySingle
          ? `Single-engine pass (${labelFor(primaryEngine)}) — faster, no cross-check.`
          : `Cross-check between ${labelFor(primaryEngine)} and ${labelFor(secondaryEngine)} — slower but catches more.`}
      </div>
    </div>
  )
}

function labelFor(engine: Engine): string {
  return engine === 'claude' ? 'Claude' : 'GPT'
}

function SegmentedRow<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { key: T; label: string }[]
  value: T
  onChange: (next: T) => void
}): JSX.Element {
  return (
    <div
      role="tablist"
      className="flex gap-1 p-1 rounded-lg bg-paper-200/60"
    >
      {options.map((option) => {
        const isActive = value === option.key
        return (
          <button
            key={option.key}
            role="tab"
            type="button"
            onClick={() => onChange(option.key)}
            className={cn(
              'flex-1 py-2 text-sm font-semibold rounded-md',
              'transition-colors duration-150 border-none cursor-pointer',
              isActive
                ? 'bg-paper-50 text-ink shadow-subtle'
                : 'bg-transparent text-ink-tertiary hover:text-ink-secondary',
            )}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
