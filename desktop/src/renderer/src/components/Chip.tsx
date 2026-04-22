import { cn } from '@/lib/utils'

export type ChipTone = 'default' | 'accent' | 'muted'

interface ChipProps {
  children: React.ReactNode
  tone?: ChipTone
  className?: string
  title?: string
}

const TONE_CLASSES: Record<ChipTone, string> = {
  default: 'border-paper-300 bg-paper-50 text-ink-tertiary',
  accent: 'border-accent/30 bg-accent/10 text-accent',
  muted: 'border-paper-300 bg-transparent text-ink-faint font-mono',
}

export function Chip({
  children,
  tone = 'default',
  className,
  title,
}: ChipProps): JSX.Element {
  return (
    <span
      title={title}
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[11px] font-medium',
        TONE_CLASSES[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}
