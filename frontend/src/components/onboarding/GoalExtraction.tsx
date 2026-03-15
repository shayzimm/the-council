import type { GoalData } from '../../types/onboarding'

interface GoalExtractionProps {
  goals: GoalData[]
  onUpdateGoal: (index: number, goal: GoalData) => void
  onRemoveGoal: (index: number) => void
  onAddGoal: () => void
  onConfirm: () => void
  isLoading?: boolean
}

const domainColors: Record<string, string> = {
  training: 'bg-aura-rust/15 text-aura-rust',
  skin: 'bg-aura-blush/20 text-aura-blush',
  wellbeing: 'bg-aura-sage/15 text-aura-sage',
  general: 'bg-aura-surface text-aura-muted',
}

function getDomainClasses(domain: string): string {
  return domainColors[domain] ?? domainColors.general
}

export function GoalExtraction({
  goals,
  onUpdateGoal,
  onRemoveGoal,
  onAddGoal,
  onConfirm,
  isLoading = false,
}: GoalExtractionProps) {
  function updateField(index: number, field: keyof GoalData, value: unknown) {
    onUpdateGoal(index, { ...goals[index], [field]: value })
  }

  return (
    <div className="max-w-lg w-full mx-auto space-y-6 px-4">
      <div className="border-l-4 border-aura-gold pl-5">
        <h2 className="font-display text-2xl text-aura-brown tracking-wide">
          Your goals
        </h2>
      </div>

      <p className="font-body text-sm text-aura-muted">
        Here are the goals I picked up. Edit, remove, or add more before we continue.
      </p>

      <div className="space-y-4">
        {goals.map((goal, index) => (
          <div
            key={index}
            className="rounded-2xl bg-aura-white border border-aura-surface shadow-sm p-5 space-y-3
                       transition-shadow hover:shadow-md"
          >
            {/* Header row: title + remove */}
            <div className="flex items-start gap-3">
              <input
                type="text"
                value={goal.title}
                onChange={(e) => updateField(index, 'title', e.target.value)}
                className="flex-1 font-body text-sm text-aura-brown bg-transparent border-b
                           border-aura-surface focus:border-aura-gold focus:outline-none
                           transition-colors pb-0.5"
              />
              <button
                onClick={() => onRemoveGoal(index)}
                aria-label={`Remove goal: ${goal.title}`}
                className="text-aura-muted hover:text-aura-rust transition-colors p-1 -mt-0.5"
              >
                <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <line x1="4" y1="4" x2="12" y2="12" />
                  <line x1="12" y1="4" x2="4" y2="12" />
                </svg>
              </button>
            </div>

            {/* Tags row */}
            <div className="flex flex-wrap items-center gap-2">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-body font-medium ${getDomainClasses(goal.domain)}`}>
                {goal.domain}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-body font-medium bg-aura-surface text-aura-muted">
                {goal.goal_type === 'north_star' ? 'North Star' : 'Milestone'}
              </span>
            </div>

            {/* Optional target value + unit */}
            <div className="flex gap-3">
              <div className="flex-1 space-y-1">
                <label className="font-body text-xs text-aura-muted uppercase tracking-wider">
                  Target
                </label>
                <input
                  type="number"
                  value={goal.target_value ?? ''}
                  onChange={(e) =>
                    updateField(
                      index,
                      'target_value',
                      e.target.value ? Number(e.target.value) : null,
                    )
                  }
                  placeholder="—"
                  className="w-full rounded-lg bg-aura-cream border border-aura-surface px-3 py-2
                             font-body text-sm text-aura-brown focus:outline-none focus:ring-2
                             focus:ring-aura-gold/40 transition-shadow"
                />
              </div>
              <div className="flex-1 space-y-1">
                <label className="font-body text-xs text-aura-muted uppercase tracking-wider">
                  Unit
                </label>
                <input
                  type="text"
                  value={goal.target_unit ?? ''}
                  onChange={(e) =>
                    updateField(index, 'target_unit', e.target.value || null)
                  }
                  placeholder="e.g. kg, reps"
                  className="w-full rounded-lg bg-aura-cream border border-aura-surface px-3 py-2
                             font-body text-sm text-aura-brown focus:outline-none focus:ring-2
                             focus:ring-aura-gold/40 transition-shadow"
                />
              </div>
            </div>

            {/* Deadline */}
            <div className="space-y-1">
              <label className="font-body text-xs text-aura-muted uppercase tracking-wider">
                Deadline
              </label>
              <input
                type="date"
                value={goal.deadline ?? ''}
                onChange={(e) =>
                  updateField(index, 'deadline', e.target.value || null)
                }
                className="w-full rounded-lg bg-aura-cream border border-aura-surface px-3 py-2
                           font-body text-sm text-aura-brown focus:outline-none focus:ring-2
                           focus:ring-aura-gold/40 transition-shadow"
              />
            </div>
          </div>
        ))}
      </div>

      {/* Add goal */}
      <button
        onClick={onAddGoal}
        className="w-full py-3 rounded-2xl border-2 border-dashed border-aura-surface
                   font-body text-sm text-aura-muted hover:border-aura-gold hover:text-aura-gold
                   transition-colors"
      >
        + Add a goal
      </button>

      {/* Confirm */}
      <button
        onClick={onConfirm}
        disabled={goals.length === 0 || isLoading}
        className="px-6 py-2.5 bg-aura-gold text-aura-brown font-body font-medium
                   rounded-full shadow-sm transition-all duration-200
                   hover:shadow-md hover:brightness-105 active:scale-[0.98]
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Saving...' : 'Confirm goals'}
      </button>
    </div>
  )
}
