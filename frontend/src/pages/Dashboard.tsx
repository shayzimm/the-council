import { Link } from 'react-router-dom'
import { StatPill } from '../components/StatPill'
import { StreakChip } from '../components/StreakChip'

const today = new Date().toLocaleDateString('en-AU', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})

// Static placeholder data — replaced with live data in a future sub-project
const WHOOP = { recovery: 74, hrv: '62ms', sleep: 87 }

const TASKS = [
  { label: 'Upper body — moderate intensity', agent: 'Rex' },
  { label: 'Tret night', agent: 'Celeste' },
  { label: '10 min NSDR', agent: 'Sage' },
]

const STREAKS = [
  { label: 'Training', days: 12 },
  { label: 'Skincare', days: 6 },
  { label: 'Check-ins', days: 3 },
]

const QUICK_ACCESS = [
  { label: 'Rex', to: '/council' },
  { label: 'Celeste', to: '/council' },
  { label: 'Sage', to: '/council' },
  { label: 'The Council', to: '/council' },
]

export default function Dashboard() {
  return (
    <div className="flex flex-col gap-6">

      {/* Greeting */}
      <div>
        <h1 className="font-display text-3xl text-aura-brown">Good morning, Shay</h1>
        <p className="font-body text-sm text-aura-muted mt-1">{today}</p>
        <p className="font-body text-sm text-aura-muted italic mt-0.5">
          Rest is as productive as effort.
        </p>
      </div>

      {/* Check-in prompt */}
      <Link
        to="/checkin"
        className="block border-l-[3px] border-aura-blush pl-4 py-3 hover:bg-aura-surface/50 rounded-r-lg transition-colors"
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="font-body text-sm font-medium text-aura-brown">Morning check-in</p>
            <p className="font-body text-xs text-aura-muted">~2 minutes</p>
          </div>
          <span className="text-aura-blush text-lg">→</span>
        </div>
      </Link>

      {/* Whoop snapshot */}
      <div className="border-l-[3px] border-aura-gold pl-4 py-3">
        <p className="font-body text-xs text-aura-muted uppercase tracking-wider mb-3">Whoop</p>
        <div className="flex gap-8">
          <StatPill label="Recovery" value={WHOOP.recovery} unit="%" />
          <StatPill label="HRV" value={WHOOP.hrv} />
          <StatPill label="Sleep" value={WHOOP.sleep} unit="%" />
        </div>
      </div>

      {/* Today's tasks */}
      <div>
        <p className="font-body text-xs text-aura-muted uppercase tracking-wider mb-3">Today</p>
        <ul className="flex flex-col gap-2.5">
          {TASKS.map((task) => (
            <li key={task.label} className="flex items-baseline gap-2">
              <span className="font-body text-sm text-aura-brown">{task.label}</span>
              <span className="font-body text-xs text-aura-muted">— {task.agent}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Active streaks */}
      <div>
        <p className="font-body text-xs text-aura-muted uppercase tracking-wider mb-3">Streaks</p>
        <div className="flex flex-wrap gap-2">
          {STREAKS.map((streak) => (
            <StreakChip key={streak.label} label={streak.label} days={streak.days} />
          ))}
        </div>
      </div>

      {/* Quick access */}
      <div>
        <p className="font-body text-xs text-aura-muted uppercase tracking-wider mb-3">Quick Access</p>
        <div className="flex flex-wrap gap-2">
          {QUICK_ACCESS.map(({ label, to }) => (
            <Link
              key={label}
              to={to}
              className="font-body text-sm text-aura-brown bg-aura-surface hover:bg-aura-blush/20 px-4 py-2 rounded-full transition-colors"
            >
              {label}
            </Link>
          ))}
        </div>
      </div>

      {/* This week at a glance */}
      <div className="border-l-[3px] border-aura-surface pl-4 py-3">
        <p className="font-body text-xs text-aura-muted uppercase tracking-wider mb-3">This Week</p>
        <div className="flex gap-8">
          <div>
            <p className="font-display text-xl text-aura-brown font-semibold">3/5</p>
            <p className="font-body text-xs text-aura-muted">Check-ins</p>
          </div>
          <div>
            <p className="font-display text-xl text-aura-brown font-semibold">4</p>
            <p className="font-body text-xs text-aura-muted">Workouts</p>
          </div>
          <div>
            <p className="font-display text-xl text-aura-brown font-semibold">7.4</p>
            <p className="font-body text-xs text-aura-muted">Avg mood</p>
          </div>
        </div>
      </div>

    </div>
  )
}
