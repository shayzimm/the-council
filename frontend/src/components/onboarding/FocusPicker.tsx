import { useState } from 'react'
import type { GoalData } from '../../types/onboarding'

interface FocusPickerProps {
  goals: GoalData[]
  onConfirm: (focusIndices: number[]) => void
  isLoading?: boolean
}

const MAX_FOCUS = 3

const domainColors: Record<string, string> = {
  training: 'bg-aura-rust/15 text-aura-rust',
  skin: 'bg-aura-blush/20 text-aura-blush',
  wellbeing: 'bg-aura-sage/15 text-aura-sage',
  general: 'bg-aura-surface text-aura-muted',
}

function getDomainClasses(domain: string): string {
  return domainColors[domain] ?? domainColors.general
}

export function FocusPicker({
  goals,
  onConfirm,
  isLoading = false,
}: FocusPickerProps) {
  const [selected, setSelected] = useState<number[]>([])

  function toggle(index: number) {
    setSelected((prev) => {
      if (prev.includes(index)) {
        return prev.filter((i) => i !== index)
      }
      if (prev.length >= MAX_FOCUS) return prev
      return [...prev, index]
    })
  }

  return (
    <div className="max-w-lg w-full mx-auto space-y-6 px-4">
      <div className="border-l-4 border-aura-gold pl-5">
        <h2 className="font-display text-2xl text-aura-brown tracking-wide">
          What matters most right now?
        </h2>
      </div>

      <p className="font-body text-sm text-aura-muted">
        Pick up to {MAX_FOCUS} goals to focus on first. You can change these any time.
      </p>

      {/* Selection counter */}
      <p className="font-body text-sm text-aura-brown">
        <span className="font-medium">{selected.length}</span> of {MAX_FOCUS} selected
      </p>

      <div className="space-y-3">
        {goals.map((goal, index) => {
          const isSelected = selected.includes(index)
          return (
            <button
              key={index}
              type="button"
              onClick={() => toggle(index)}
              className={[
                'w-full text-left rounded-2xl border-2 p-4 transition-all duration-200',
                isSelected
                  ? 'border-aura-gold bg-aura-white shadow-md'
                  : 'border-aura-surface bg-aura-white hover:border-aura-gold/40 hover:shadow-sm',
              ].join(' ')}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="space-y-1.5">
                  <p className="font-body text-sm text-aura-brown font-medium">
                    {goal.title}
                  </p>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-body font-medium ${getDomainClasses(goal.domain)}`}>
                      {goal.domain}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-body font-medium bg-aura-surface text-aura-muted">
                      {goal.goal_type === 'north_star' ? 'North Star' : 'Milestone'}
                    </span>
                  </div>
                </div>

                {/* Check indicator */}
                <div
                  className={[
                    'w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors',
                    isSelected
                      ? 'border-aura-gold bg-aura-gold'
                      : 'border-aura-surface',
                  ].join(' ')}
                >
                  {isSelected && (
                    <svg aria-hidden="true" width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="#2C2420" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 7 6 10 11 4" />
                    </svg>
                  )}
                </div>
              </div>
            </button>
          )
        })}
      </div>

      <button
        onClick={() => onConfirm(selected)}
        disabled={selected.length === 0 || isLoading}
        className="px-6 py-2.5 bg-aura-gold text-aura-brown font-body font-medium
                   rounded-full shadow-sm transition-all duration-200
                   hover:shadow-md hover:brightness-105 active:scale-[0.98]
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Saving...' : 'Set my focus'}
      </button>
    </div>
  )
}
