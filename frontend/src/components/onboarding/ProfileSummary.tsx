import type { GoalData } from '../../types/onboarding'

interface ProfileSummaryProps {
  extractedData: Record<string, unknown>
  goals: GoalData[]
  onConfirm: () => void
  onEdit: (section: string) => void
  isLoading?: boolean
}

/** Maps profile keys to logical sections for display grouping. */
const sectionMapping: Record<string, string> = {
  training_frequency: 'Lifestyle',
  training_type: 'Lifestyle',
  training_experience: 'Lifestyle',
  work_status: 'Lifestyle',
  study_status: 'Lifestyle',
  location: 'Lifestyle',
  skin_type: 'Skin',
  skin_concerns: 'Skin',
  current_routine_brief: 'Skin',
  active_medications: 'Skin',
  stress_baseline: 'Wellbeing',
  anxiety_baseline: 'Wellbeing',
  sleep_baseline: 'Wellbeing',
  energy_baseline: 'Wellbeing',
  supplements: 'Other',
  cycle_length: 'Other',
  cycle_tracking: 'Other',
  additional_notes: 'Other',
}

function getSectionForKey(key: string): string {
  return sectionMapping[key] ?? 'Other'
}

function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (Array.isArray(value)) return value.length > 0 ? value.join(', ') : '—'
  return String(value)
}

const domainColors: Record<string, string> = {
  training: 'border-aura-rust',
  skin: 'border-aura-blush',
  wellbeing: 'border-aura-sage',
  general: 'border-aura-muted',
}

export function ProfileSummary({
  extractedData,
  goals,
  onConfirm,
  onEdit,
  isLoading = false,
}: ProfileSummaryProps) {
  // Group profile data by section
  const sections: Record<string, [string, unknown][]> = {}
  for (const [key, value] of Object.entries(extractedData)) {
    // Skip nested non-array objects, but allow arrays and primitives
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) continue
    const section = getSectionForKey(key)
    if (!sections[section]) sections[section] = []
    sections[section].push([key, value])
  }

  // Group goals by domain
  const goalsByDomain: Record<string, GoalData[]> = {}
  for (const goal of goals) {
    const domain = goal.domain || 'general'
    if (!goalsByDomain[domain]) goalsByDomain[domain] = []
    goalsByDomain[domain].push(goal)
  }

  const sectionOrder = ['Lifestyle', 'Skin', 'Wellbeing', 'Other']

  return (
    <div className="max-w-lg w-full mx-auto space-y-8 px-4">
      <div className="border-l-4 border-aura-gold pl-5">
        <h2 className="font-display text-2xl text-aura-brown tracking-wide">
          Your profile
        </h2>
      </div>

      <p className="font-body text-sm text-aura-muted">
        Take a final look before we wrap up. You can always update things later.
      </p>

      {/* Profile sections */}
      {sectionOrder.map((sectionName) => {
        const fields = sections[sectionName]
        if (!fields || fields.length === 0) return null

        return (
          <div
            key={sectionName}
            className="rounded-2xl bg-aura-white border border-aura-surface shadow-sm p-5 space-y-3"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-display text-lg text-aura-brown">
                {sectionName}
              </h3>
              <button
                onClick={() => onEdit(sectionName.toLowerCase())}
                className="font-body text-xs text-aura-gold hover:text-aura-brown transition-colors"
              >
                Edit
              </button>
            </div>

            <div className="divide-y divide-aura-surface">
              {fields.map(([key, value]) => (
                <div key={key} className="flex justify-between items-baseline py-2 gap-4">
                  <span className="font-body text-xs text-aura-muted uppercase tracking-wider">
                    {formatLabel(key)}
                  </span>
                  <span className="font-body text-sm text-aura-brown text-right">
                    {formatValue(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )
      })}

      {/* Goals by domain */}
      {Object.keys(goalsByDomain).length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-lg text-aura-brown">Goals</h3>
            <button
              onClick={() => onEdit('goals')}
              className="font-body text-xs text-aura-gold hover:text-aura-brown transition-colors"
            >
              Edit
            </button>
          </div>

          {Object.entries(goalsByDomain).map(([domain, domainGoals]) => (
            <div key={domain} className="space-y-2">
              <p className="font-body text-xs text-aura-muted uppercase tracking-wider">
                {domain}
              </p>
              {domainGoals.map((goal, idx) => (
                <div
                  key={idx}
                  className={`rounded-xl border-l-4 ${domainColors[domain] ?? domainColors.general}
                              bg-aura-white border border-aura-surface shadow-sm p-4`}
                >
                  <p className="font-body text-sm text-aura-brown font-medium">
                    {goal.title}
                  </p>
                  <div className="flex flex-wrap gap-2 mt-1.5">
                    <span className="font-body text-xs text-aura-muted">
                      {goal.goal_type === 'north_star' ? 'North Star' : 'Milestone'}
                    </span>
                    {goal.target_value != null && (
                      <span className="font-body text-xs text-aura-muted">
                        Target: {goal.target_value} {goal.target_unit ?? ''}
                      </span>
                    )}
                    {goal.deadline && (
                      <span className="font-body text-xs text-aura-muted">
                        By {goal.deadline}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Confirm CTA */}
      <button
        onClick={onConfirm}
        disabled={isLoading}
        className="w-full py-3 bg-aura-gold text-aura-brown font-body font-medium
                   rounded-full shadow-sm transition-all duration-200
                   hover:shadow-md hover:brightness-105 active:scale-[0.98]
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Finalising...' : 'Everything looks good'}
      </button>
    </div>
  )
}
