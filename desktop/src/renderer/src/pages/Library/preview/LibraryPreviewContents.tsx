import { useCallback } from 'react'
import { cn } from '@/lib/utils'
import type { TocEntry } from './extractToc'

interface LibraryPreviewContentsProps {
  entries: TocEntry[]
  activeSlug: string | null
  scrollRootRef: React.RefObject<HTMLElement>
}

export default function LibraryPreviewContents({
  entries,
  activeSlug,
  scrollRootRef,
}: LibraryPreviewContentsProps): JSX.Element | null {
  const handleJump = useCallback(
    (slug: string) => {
      const root = scrollRootRef.current
      if (!root) return
      const target = root.querySelector<HTMLElement>(`#${CSS.escape(slug)}`)
      if (!target) return
      const rootRect = root.getBoundingClientRect()
      const targetRect = target.getBoundingClientRect()
      const offset = targetRect.top - rootRect.top + root.scrollTop - 24
      root.scrollTo({ top: offset, behavior: 'smooth' })
    },
    [scrollRootRef],
  )

  if (entries.length === 0) return null

  return (
    <aside className="w-60 shrink-0 hidden lg:block">
      <nav className="sticky top-6 max-h-[calc(100vh-6rem)] overflow-y-auto pr-2">
        <div className="text-[11px] font-semibold text-ink-tertiary uppercase tracking-wider mb-3 px-2">
          Contents
        </div>
        <ul className="space-y-0.5">
          {entries.map((entry, index) => (
            <li key={`${entry.slug}-${index}`}>
              <button
                type="button"
                onClick={() => handleJump(entry.slug)}
                className={cn(
                  'w-full text-left px-2 py-1 rounded-md text-xs leading-snug',
                  'border-l-2 transition-colors duration-100 cursor-pointer',
                  'bg-transparent',
                  activeSlug === entry.slug
                    ? 'border-accent text-accent font-medium bg-accent/5'
                    : 'border-transparent text-ink-tertiary hover:text-ink-secondary hover:bg-paper-200/60',
                )}
                style={{ paddingLeft: `${0.5 + (entry.level - 1) * 0.75}rem` }}
                title={entry.text}
              >
                <span className="block truncate">{entry.text}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  )
}
