interface StreakChipProps {
  label: string
  days: number
}

export function StreakChip({ label, days }: StreakChipProps) {
  return (
    <div className="inline-flex items-center gap-1.5 bg-aura-surface rounded-full px-3 py-1.5">
      <span className="font-body text-sm text-aura-brown">{label}</span>
      <span className="font-body text-sm text-aura-gold font-medium">{days}d</span>
    </div>
  )
}
