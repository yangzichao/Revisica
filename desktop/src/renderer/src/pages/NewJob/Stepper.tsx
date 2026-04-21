import { Check, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { WizardStep } from './types'

interface StepMeta {
  id: WizardStep
  label: string
}

const STEPS: StepMeta[] = [
  { id: 1, label: 'Input' },
  { id: 2, label: 'Review plan' },
]

interface StepperProps {
  currentStep: WizardStep
  onStepClick: (step: WizardStep) => void
}

// Circle is 24px (w-6 h-6); its vertical center sits at 12px. We anchor
// every column to items-start so `mt-3` (12px) lines the connector up
// exactly with that center regardless of label height.
const CIRCLE_CENTER_OFFSET = 'mt-3'

export default function Stepper({
  currentStep,
  onStepClick,
}: StepperProps): JSX.Element {
  return (
    <div className="w-full py-6">
      <div className="flex items-start justify-between max-w-md mx-auto">
        {STEPS.map((step, index) => {
          const nodeState: 'completed' | 'active' | 'upcoming' =
            step.id < currentStep
              ? 'completed'
              : step.id === currentStep
                ? 'active'
                : 'upcoming'
          const isLast = index === STEPS.length - 1

          return (
            <div key={step.id} className="flex items-start flex-1 last:flex-none">
              <StepNode
                step={step}
                state={nodeState}
                onClick={() => {
                  if (nodeState === 'completed') {
                    onStepClick(step.id)
                  }
                }}
              />
              {!isLast && <StepConnector traversed={step.id < currentStep} />}
            </div>
          )
        })}
      </div>
    </div>
  )

  function StepConnector({ traversed }: { traversed: boolean }): JSX.Element {
    return (
      <div
        className={cn('flex items-center flex-1 mx-2', CIRCLE_CENTER_OFFSET)}
        aria-hidden="true"
      >
        <div
          className={cn(
            'flex-1 transition-colors duration-150',
            traversed
              ? 'h-px bg-accent'
              : 'border-t border-dashed border-paper-400',
          )}
        />
        <ChevronRight
          size={12}
          strokeWidth={2}
          className={cn(
            'shrink-0 -ml-1',
            traversed ? 'text-accent' : 'text-ink-faint',
          )}
        />
      </div>
    )
  }
}

function StepNode({
  step,
  state,
  onClick,
}: {
  step: StepMeta
  state: 'completed' | 'active' | 'upcoming'
  onClick: () => void
}): JSX.Element {
  return (
    <div className="flex flex-col items-center gap-2 shrink-0">
      <button
        type="button"
        onClick={onClick}
        disabled={state !== 'completed'}
        aria-current={state === 'active' ? 'step' : undefined}
        className={cn(
          'relative w-6 h-6 rounded-full flex items-center justify-center',
          'text-[11px] font-semibold transition-all duration-150 border',
          state === 'completed' &&
            'bg-accent text-white border-accent cursor-pointer hover:bg-accent-hover',
          state === 'active' &&
            'bg-accent text-white border-accent ring-4 ring-accent/15 cursor-default',
          state === 'upcoming' &&
            'bg-paper-50 text-ink-faint border-paper-300 cursor-not-allowed',
        )}
      >
        {state === 'completed' ? <Check size={12} strokeWidth={3} /> : step.id}
      </button>
      <span
        className={cn(
          'font-serif text-xs whitespace-nowrap',
          state === 'active' && 'text-ink font-semibold',
          state === 'completed' && 'text-ink',
          state === 'upcoming' && 'text-ink-faint',
        )}
      >
        {step.label}
      </span>
    </div>
  )
}
