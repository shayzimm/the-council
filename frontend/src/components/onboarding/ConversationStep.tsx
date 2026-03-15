import { useState, type ReactNode } from 'react'

interface ConversationStepProps {
  title: string
  prompt: string
  topic: string
  onSubmit: (rawInput: string) => Promise<Record<string, unknown>>
  onConfirm: (extractedData: Record<string, unknown>) => Promise<void>
  isLoading?: boolean
}

function renderFieldInput(
  key: string,
  value: unknown,
  onChange: (key: string, value: unknown) => void,
): ReactNode {
  if (typeof value === 'boolean') {
    return (
      <select
        value={value ? 'true' : 'false'}
        onChange={(e) => onChange(key, e.target.value === 'true')}
        className="w-full rounded-lg bg-aura-cream border border-aura-surface px-3 py-2
                   font-body text-sm text-aura-brown focus:outline-none focus:ring-2
                   focus:ring-aura-gold/40 transition-shadow"
      >
        <option value="true">Yes</option>
        <option value="false">No</option>
      </select>
    )
  }

  if (typeof value === 'number') {
    return (
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(key, Number(e.target.value))}
        className="w-full rounded-lg bg-aura-cream border border-aura-surface px-3 py-2
                   font-body text-sm text-aura-brown focus:outline-none focus:ring-2
                   focus:ring-aura-gold/40 transition-shadow"
      />
    )
  }

  return (
    <input
      type="text"
      value={String(value ?? '')}
      onChange={(e) => onChange(key, e.target.value)}
      className="w-full rounded-lg bg-aura-cream border border-aura-surface px-3 py-2
                 font-body text-sm text-aura-brown focus:outline-none focus:ring-2
                 focus:ring-aura-gold/40 transition-shadow"
    />
  )
}

function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function ConversationStep({
  title,
  prompt,
  onSubmit,
  onConfirm,
  isLoading = false,
}: ConversationStepProps) {
  const [phase, setPhase] = useState<'input' | 'confirm'>('input')
  const [rawInput, setRawInput] = useState('')
  const [extracted, setExtracted] = useState<Record<string, unknown>>({})

  async function handleSubmit() {
    if (!rawInput.trim() || isLoading) return
    const data = await onSubmit(rawInput)
    setExtracted(data)
    setPhase('confirm')
  }

  function handleFieldChange(key: string, value: unknown) {
    setExtracted((prev) => ({ ...prev, [key]: value }))
  }

  async function handleConfirm() {
    if (isLoading) return
    await onConfirm(extracted)
  }

  return (
    <div className="max-w-lg w-full mx-auto space-y-6 px-4">
      {/* Aurore prompt header */}
      <div className="border-l-4 border-aura-gold pl-5">
        <h2 className="font-display text-2xl text-aura-brown tracking-wide">
          {title}
        </h2>
      </div>

      {phase === 'input' && (
        <div className="space-y-5 animate-fade-in">
          <p className="font-body text-base text-aura-brown leading-relaxed">
            {prompt}
          </p>

          <textarea
            value={rawInput}
            onChange={(e) => setRawInput(e.target.value)}
            rows={5}
            placeholder="Tell me in your own words..."
            className="w-full rounded-xl bg-aura-surface border-none px-4 py-3
                       font-body text-sm text-aura-brown placeholder:text-aura-muted
                       resize-y focus:outline-none focus:ring-2 focus:ring-aura-gold/40
                       transition-shadow"
          />

          <button
            onClick={handleSubmit}
            disabled={!rawInput.trim() || isLoading}
            className="px-6 py-2.5 bg-aura-blush text-aura-white font-body font-medium
                       rounded-full shadow-sm transition-all duration-200
                       hover:shadow-md hover:brightness-105 active:scale-[0.98]
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Processing...' : 'Continue'}
          </button>
        </div>
      )}

      {phase === 'confirm' && (
        <div className="space-y-5 animate-fade-in">
          <p className="font-body text-sm text-aura-muted">
            Here's what I gathered — feel free to adjust anything.
          </p>

          <div className="rounded-2xl bg-aura-white border border-aura-surface shadow-sm p-5 space-y-4">
            {Object.entries(extracted).map(([key, value]) => {
              if (Array.isArray(value)) {
                return (
                  <div key={key} className="space-y-1">
                    <label className="font-body text-xs text-aura-muted uppercase tracking-wider">
                      {formatLabel(key)}
                    </label>
                    <input
                      type="text"
                      value={(value as string[]).join(', ')}
                      onChange={(e) =>
                        handleFieldChange(
                          key,
                          e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                        )
                      }
                      className="w-full rounded-lg bg-aura-cream border border-aura-surface px-3 py-2
                                 font-body text-sm text-aura-brown focus:outline-none focus:ring-2
                                 focus:ring-aura-gold/40 transition-shadow"
                    />
                  </div>
                )
              }

              if (value !== null && typeof value === 'object') return null

              return (
                <div key={key} className="space-y-1">
                  <label className="font-body text-xs text-aura-muted uppercase tracking-wider">
                    {formatLabel(key)}
                  </label>
                  {renderFieldInput(key, value, handleFieldChange)}
                </div>
              )
            })}
          </div>

          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className="px-6 py-2.5 bg-aura-gold text-aura-brown font-body font-medium
                       rounded-full shadow-sm transition-all duration-200
                       hover:shadow-md hover:brightness-105 active:scale-[0.98]
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Saving...' : 'Looks good'}
          </button>
        </div>
      )}
    </div>
  )
}
