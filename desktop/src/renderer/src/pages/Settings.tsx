import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'

type BackendMode = 'cli' | 'api' | 'auto'

const BACKEND_MODES: { key: BackendMode; label: string; description: string }[] = [
  { key: 'cli', label: 'CLI', description: 'CLI subscription' },
  { key: 'api', label: 'API', description: 'HTTP API keys' },
  { key: 'auto', label: 'Auto', description: 'Prefer CLI, fallback API' },
]

export default function Settings({
  apiBase,
  apiToken,
}: {
  apiBase: string
  apiToken: string
}): JSX.Element {
  const [backendMode, setBackendMode] = useState<BackendMode>('auto')
  const [isBackendReady, setIsBackendReady] = useState(false)

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
  }, [apiBase, apiToken])

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-lg mx-auto px-8 py-12">
        <header className="mb-10">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            Settings
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Application configuration
          </p>
        </header>

        {/* Backend section */}
        <section className="mb-10">
          <h2 className="font-serif text-lg font-semibold text-ink mb-6">
            Backend
          </h2>

          {/* API Server status */}
          <div className="card px-5 py-4 mb-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-ink">API Server</div>
                <div className="text-xs text-ink-faint font-mono mt-0.5">
                  {apiBase}
                </div>
              </div>
              <div
                className={cn(
                  'w-2.5 h-2.5 rounded-full shrink-0',
                  isBackendReady ? 'bg-success' : 'bg-danger',
                )}
              />
            </div>
          </div>

          {/* Backend mode */}
          <div className="card px-5 py-5">
            <div className="text-sm font-medium text-ink mb-1">
              Backend Mode
            </div>
            <div className="text-xs text-ink-faint mb-4">
              How Revisica connects to AI providers
            </div>

            <div className="flex gap-1 p-1 rounded-lg bg-paper-200/60">
              {BACKEND_MODES.map((modeOption) => (
                <button
                  key={modeOption.key}
                  onClick={() => setBackendMode(modeOption.key)}
                  className={cn(
                    'flex-1 py-2.5 flex flex-col items-center gap-0.5',
                    'text-sm font-semibold rounded-md',
                    'transition-colors duration-150 border-none cursor-pointer',
                    modeOption.key === backendMode
                      ? 'bg-paper-50 text-ink shadow-subtle'
                      : 'bg-transparent text-ink-tertiary',
                  )}
                >
                  {modeOption.label}
                  <span className="text-[10px] font-normal opacity-70">
                    {modeOption.description}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Data section */}
        <section>
          <h2 className="font-serif text-lg font-semibold text-ink mb-6">
            Data
          </h2>
          <div className="card divide-y divide-paper-300/60">
            <SettingsRow label="Config directory" value="~/.revisica/" />
            <SettingsRow label="Review output" value="reviews/" />
          </div>
        </section>
      </div>
    </div>
  )
}

function SettingsRow({
  label,
  value,
}: {
  label: string
  value: string
}): JSX.Element {
  return (
    <div className="flex items-center justify-between px-5 py-4">
      <div className="text-sm font-medium text-ink">{label}</div>
      <div className="text-xs text-ink-faint font-mono">{value}</div>
    </div>
  )
}
