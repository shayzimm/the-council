import { useEffect, useState } from 'react'
import type { AgentMessage } from '../../types/onboarding'

interface CouncilIntroductionProps {
  messages: AgentMessage[]
  onComplete: () => void
}

const STAGGER_DELAY = 500

export function CouncilIntroduction({
  messages,
  onComplete,
}: CouncilIntroductionProps) {
  const [visibleCount, setVisibleCount] = useState(0)

  useEffect(() => {
    if (visibleCount >= messages.length) return

    const timer = setTimeout(() => {
      setVisibleCount((c) => c + 1)
    }, STAGGER_DELAY)

    return () => clearTimeout(timer)
  }, [visibleCount, messages.length])

  const allRevealed = visibleCount >= messages.length

  return (
    <div className="max-w-lg w-full mx-auto space-y-6 px-4">
      <div className="border-l-4 border-aura-gold pl-5">
        <h2 className="font-display text-2xl text-aura-brown tracking-wide">
          Meet The Council
        </h2>
      </div>

      <div className="space-y-4">
        {messages.map((msg, index) => (
          <div
            key={msg.agent_name}
            className={[
              'rounded-2xl bg-aura-white border border-aura-surface shadow-sm p-5',
              'border-l-4 transition-all duration-500',
              index < visibleCount
                ? 'opacity-100 translate-y-0'
                : 'opacity-0 translate-y-4 pointer-events-none',
            ].join(' ')}
            style={{ borderLeftColor: msg.accent_color }}
          >
            <h3
              className="font-display text-lg mb-2"
              style={{ color: msg.accent_color }}
            >
              {msg.display_name}
            </h3>
            <p className="font-body text-sm text-aura-brown leading-relaxed">
              {msg.message}
            </p>
          </div>
        ))}
      </div>

      {allRevealed && (
        <div className="animate-fade-in">
          <button
            onClick={onComplete}
            className="px-6 py-2.5 bg-aura-gold text-aura-brown font-body font-medium
                       rounded-full shadow-sm transition-all duration-200
                       hover:shadow-md hover:brightness-105 active:scale-[0.98]"
          >
            Meet your dashboard
          </button>
        </div>
      )}
    </div>
  )
}
