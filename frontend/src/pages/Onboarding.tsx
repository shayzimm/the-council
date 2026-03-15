import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useOnboarding } from '../hooks/useOnboarding'
import { OnboardingWelcome } from '../components/onboarding/OnboardingWelcome'
import { ConversationStep } from '../components/onboarding/ConversationStep'
import { GoalExtraction } from '../components/onboarding/GoalExtraction'
import { FocusPicker } from '../components/onboarding/FocusPicker'
import { ProfileSummary } from '../components/onboarding/ProfileSummary'
import { CouncilIntroduction } from '../components/onboarding/CouncilIntroduction'
import type { GoalData } from '../types/onboarding'

const TOPIC_PROMPTS: Record<string, { title: string; prompt: string; topic: string }> = {
  TOPIC_LIFESTYLE: {
    title: 'Your week',
    prompt:
      "Tell me about your week — training, work, study, whatever paints the picture.",
    topic: 'lifestyle',
  },
  TOPIC_SKIN: {
    title: 'Skin & routine',
    prompt:
      "Now skin. What's your current routine, and what are you dealing with? Don't worry about being precise — Celeste will dig into the details once she's had a chance to get to know your skin.",
    topic: 'skin',
  },
  TOPIC_WELLBEING: {
    title: 'Your headspace',
    prompt:
      "How's your headspace been lately? Stress, anxiety, sleep — give me the honest version, not the polished one.",
    topic: 'wellbeing',
  },
  TOPIC_OTHER: {
    title: 'Anything else',
    prompt:
      "Anything else I should know? Medications, supplements, injuries, things that affect your day-to-day — or skip this if you've covered it.",
    topic: 'other',
  },
}

const GOAL_PROMPTS: Record<string, { title: string; prompt: string; topic: string }> = {
  TOPIC_LIFESTYLE_GOALS: {
    title: 'Training goals',
    prompt:
      "What are you working toward with your body and training right now? Big picture is fine — we'll get specific over time.",
    topic: 'lifestyle_goals',
  },
  TOPIC_SKIN_GOALS: {
    title: 'Skin goals',
    prompt: 'If you could change one thing about your skin, what would it be?',
    topic: 'skin_goals',
  },
  TOPIC_WELLBEING_GOALS: {
    title: 'Wellbeing goals',
    prompt:
      "What does feeling good look like for you? Not perfect — just genuinely good.",
    topic: 'wellbeing_goals',
  },
}

export default function Onboarding() {
  const navigate = useNavigate()
  const {
    state,
    startOnboarding,
    submitTopicResponse,
    confirmTopic,
    completeOnboarding,
    nextStep,
    skipStep,
    addGoals,
    updateGoal,
    removeGoal,
    setFocusGoals,
  } = useOnboarding()

  const { step, isLoading, error, goals, extractedData, agentMessages } = state

  // Flatten all extracted data into a single object for ProfileSummary
  const allExtractedData: Record<string, unknown> = {}
  for (const topicData of Object.values(extractedData)) {
    if (topicData && typeof topicData === 'object' && !Array.isArray(topicData)) {
      Object.assign(allExtractedData, topicData)
    }
  }

  return (
    <div className="min-h-screen bg-aura-cream py-8">
      {/* Error banner */}
      {error && (
        <div className="max-w-lg mx-auto mb-6 px-4">
          <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3">
            <p className="font-body text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* NOT_STARTED — auto-start */}
      {step === 'NOT_STARTED' && (
        <OnboardingWelcome
          onStart={async () => {
            await startOnboarding()
          }}
        />
      )}

      {/* WELCOME */}
      {step === 'WELCOME' && <OnboardingWelcome onStart={nextStep} />}

      {/* TOPIC steps (lifestyle, skin, wellbeing, other) */}
      {step in TOPIC_PROMPTS && (
        <div className="animate-fade-in">
          <ConversationStep
            title={TOPIC_PROMPTS[step].title}
            prompt={TOPIC_PROMPTS[step].prompt}
            topic={TOPIC_PROMPTS[step].topic}
            onSubmit={(rawInput) =>
              submitTopicResponse(TOPIC_PROMPTS[step].topic, rawInput)
            }
            onConfirm={async (data) => {
              await confirmTopic(TOPIC_PROMPTS[step].topic, data)
            }}
            isLoading={isLoading}
          />
          {step === 'TOPIC_OTHER' && (
            <div className="max-w-lg mx-auto mt-4 px-4">
              <button
                onClick={skipStep}
                className="font-body text-sm text-aura-muted hover:text-aura-brown transition-colors"
              >
                Skip this step
              </button>
            </div>
          )}
        </div>
      )}

      {/* GOAL steps */}
      {step in GOAL_PROMPTS && (
        <div className="animate-fade-in">
          <GoalConversation
            goalPrompt={GOAL_PROMPTS[step]}
            goals={goals}
            isLoading={isLoading}
            onSubmit={submitTopicResponse}
            onConfirmGoals={async (extractedGoals) => {
              await confirmTopic(GOAL_PROMPTS[step].topic, {}, extractedGoals)
            }}
            onAddGoals={addGoals}
            onUpdateGoal={updateGoal}
            onRemoveGoal={removeGoal}
          />
        </div>
      )}

      {/* FOCUS_PICKER */}
      {step === 'FOCUS_PICKER' && (
        <div className="animate-fade-in">
          <FocusPicker
            goals={goals}
            isLoading={isLoading}
            onConfirm={(indices) => {
              setFocusGoals(indices)
              nextStep()
            }}
          />
        </div>
      )}

      {/* PROFILE_SUMMARY */}
      {step === 'PROFILE_SUMMARY' && (
        <div className="animate-fade-in">
          <ProfileSummary
            extractedData={allExtractedData}
            goals={goals}
            isLoading={isLoading}
            onConfirm={completeOnboarding}
            onEdit={() => {
              // For now, just proceed — editing will navigate back in a future iteration
            }}
          />
        </div>
      )}

      {/* COUNCIL_INTRODUCTION */}
      {step === 'COUNCIL_INTRODUCTION' && (
        <div className="animate-fade-in">
          <CouncilIntroduction
            messages={agentMessages}
            onComplete={() => navigate('/dashboard')}
          />
        </div>
      )}

      {/* COMPLETE — redirect */}
      {step === 'COMPLETE' && (() => { navigate('/dashboard'); return null })()}
    </div>
  )
}

// ---------------------------------------------------------------------------
// GoalConversation — combines the conversational prompt with goal editing
// ---------------------------------------------------------------------------

interface GoalConversationProps {
  goalPrompt: { title: string; prompt: string; topic: string }
  goals: GoalData[]
  isLoading: boolean
  onSubmit: (topic: string, rawInput: string) => Promise<Record<string, unknown>>
  onConfirmGoals: (goals: GoalData[]) => Promise<void>
  onAddGoals: (goals: GoalData[]) => void
  onUpdateGoal: (index: number, goal: GoalData) => void
  onRemoveGoal: (index: number) => void
}

function GoalConversation({
  goalPrompt,
  goals,
  isLoading,
  onSubmit,
  onConfirmGoals,
  onAddGoals,
  onUpdateGoal,
  onRemoveGoal,
}: GoalConversationProps) {
  const [phase, setPhase] = useState<'input' | 'edit'>('input')
  const [rawInput, setRawInput] = useState('')

  async function handleSubmit() {
    if (!rawInput.trim() || isLoading) return
    const result = await onSubmit(goalPrompt.topic, rawInput)
    // The extraction returns an array of goals
    const extractedGoals: GoalData[] = Array.isArray(result) ? result : []
    if (extractedGoals.length > 0) {
      onAddGoals(extractedGoals)
    }
    setPhase('edit')
  }

  // Filter goals by domain for this topic
  const domainMap: Record<string, string> = {
    lifestyle_goals: 'training',
    skin_goals: 'skin',
    wellbeing_goals: 'wellbeing',
  }
  const relevantDomain = domainMap[goalPrompt.topic]
  // Show all goals (user may have cross-domain goals), but filter to domain-relevant ones
  // for display in this step. Use the full goal list for editing.

  if (phase === 'input') {
    return (
      <div className="max-w-lg w-full mx-auto space-y-6 px-4">
        <div className="border-l-4 border-aura-gold pl-5">
          <h2 className="font-display text-2xl text-aura-brown tracking-wide">
            {goalPrompt.title}
          </h2>
        </div>

        <p className="font-body text-base text-aura-brown leading-relaxed">
          {goalPrompt.prompt}
        </p>

        <textarea
          value={rawInput}
          onChange={(e) => setRawInput(e.target.value)}
          rows={4}
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
    )
  }

  return (
    <GoalExtraction
      goals={goals}
      onUpdateGoal={onUpdateGoal}
      onRemoveGoal={onRemoveGoal}
      onAddGoal={() =>
        onAddGoals([
          {
            title: '',
            domain: relevantDomain || 'general',
            goal_type: 'milestone',
            linked_agent: 'aurore',
          },
        ])
      }
      onConfirm={() => onConfirmGoals(goals)}
      isLoading={isLoading}
    />
  )
}

