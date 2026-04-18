import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface ModeCardProps {
  icon: LucideIcon
  title: string
  description: string
  isSelected: boolean
  onClick: () => void
  disabled?: boolean
  trailing?: React.ReactNode
}

export default function ModeCard({
  icon: Icon,
  title,
  description,
  isSelected,
  onClick,
  disabled = false,
  trailing,
}: ModeCardProps): JSX.Element {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'card flex items-center gap-3 px-4 py-4 text-left w-full',
        'transition-all duration-150 cursor-pointer',
        'disabled:opacity-60 disabled:cursor-not-allowed',
        isSelected && 'border-accent/40 ring-2 ring-accent/15',
      )}
    >
      <Icon
        size={20}
        strokeWidth={1.5}
        className={isSelected ? 'text-accent' : 'text-ink-faint'}
      />
      <div className="flex-1 min-w-0">
        <div
          className={cn(
            'text-sm font-semibold',
            isSelected ? 'text-accent' : 'text-ink',
          )}
        >
          {title}
        </div>
        <div className="text-xs text-ink-tertiary mt-0.5">{description}</div>
      </div>
      {trailing}
    </button>
  )
}
