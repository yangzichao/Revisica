export default function Help(): JSX.Element {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-lg mx-auto px-8 py-12">
        <header className="mb-10">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            Help
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Revisica — Academic paper revision agent
          </p>
        </header>

        <section className="card px-6 py-5 mb-4">
          <h2 className="font-serif text-base font-semibold text-ink mb-3">
            Quick Start
          </h2>
          <ol className="list-decimal pl-5 space-y-2.5 text-sm text-ink-secondary leading-relaxed">
            <li>
              Go to <strong className="text-ink">New</strong> and drop a .tex or
              .pdf file
            </li>
            <li>
              Choose <strong className="text-ink">Polish</strong> (writing only)
              or <strong className="text-ink">Review</strong> (full analysis)
            </li>
            <li>
              Click Start — track progress in the{' '}
              <strong className="text-ink">Jobs</strong> tab
            </li>
            <li>
              Read findings in the Summary, Writing, and Math report tabs
            </li>
          </ol>
        </section>

        <section className="card px-6 py-5 mb-4">
          <h2 className="font-serif text-base font-semibold text-ink mb-3">
            Providers
          </h2>
          <p className="text-sm text-ink-secondary leading-relaxed">
            Revisica uses AI providers (Codex, Claude) to review your paper. In{' '}
            <strong className="text-ink">CLI mode</strong>, it uses your existing
            subscription via the official CLI tools. In{' '}
            <strong className="text-ink">API mode</strong>, it connects via HTTP
            API keys (configure in the Providers tab).
          </p>
        </section>

        <section className="card px-6 py-5 mb-4">
          <h2 className="font-serif text-base font-semibold text-ink mb-3">
            Review Modes
          </h2>
          <div className="space-y-3 text-sm text-ink-secondary leading-relaxed">
            <p>
              <strong className="text-ink">Polish</strong> — Writing style review
              only. Checks structure, clarity, and venue fit.
            </p>
            <p>
              <strong className="text-ink">Review</strong> — Full deep analysis.
              Writing review plus math lane (symbolic checks, proof review, claim
              verification).
            </p>
          </div>
        </section>

        <section className="card px-6 py-5">
          <h2 className="font-serif text-base font-semibold text-ink mb-2">
            About
          </h2>
          <p className="text-sm text-ink-faint">Version 0.1.0</p>
        </section>
      </div>
    </div>
  )
}
