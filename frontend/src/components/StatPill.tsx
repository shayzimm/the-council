interface StatPillProps {
  label: string
  value: string | number
  unit?: string
}

export function StatPill({ label, value, unit }: StatPillProps) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className="font-display text-xl text-aura-brown font-semibold leading-none">
        {value}{unit}
      </span>
      <span className="font-body text-xs text-aura-muted uppercase tracking-wider">
        {label}
      </span>
    </div>
  )
}
