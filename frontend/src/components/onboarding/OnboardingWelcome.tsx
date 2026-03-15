interface OnboardingWelcomeProps {
  onStart: () => void
}

export function OnboardingWelcome({ onStart }: OnboardingWelcomeProps) {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="max-w-lg w-full space-y-10">
        {/* Aurore header */}
        <div className="border-l-4 border-aura-gold pl-5">
          <h1 className="font-display text-3xl md:text-4xl text-aura-brown tracking-wide">
            Aurore
          </h1>
          <p className="font-body text-sm text-aura-gold mt-1 tracking-wider uppercase">
            Council Conductor
          </p>
        </div>

        {/* Welcome message */}
        <p className="font-body text-base md:text-lg text-aura-brown leading-relaxed">
          Hi Shay. I'm Aurore — I coordinate The Council, your personal advisory
          team. Before I introduce everyone, I'd love to understand you a little.
          This takes about five minutes, and you can always update things later.
        </p>

        {/* CTA */}
        <button
          onClick={onStart}
          className="w-full sm:w-auto px-8 py-3 bg-aura-gold text-aura-brown font-body font-medium
                     rounded-full shadow-sm transition-all duration-200
                     hover:shadow-md hover:brightness-105 active:scale-[0.98]"
        >
          Let's get started
        </button>
      </div>
    </div>
  )
}
