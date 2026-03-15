import { useReducer, useCallback } from 'react'
import type {
  OnboardingStep,
  GoalData,
  AgentMessage,
} from '../types/onboarding'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// --- Step sequence ---

const STEP_ORDER: OnboardingStep[] = [
  'NOT_STARTED',
  'WELCOME',
  'TOPIC_LIFESTYLE',
  'TOPIC_LIFESTYLE_GOALS',
  'TOPIC_SKIN',
  'TOPIC_SKIN_GOALS',
  'TOPIC_WELLBEING',
  'TOPIC_WELLBEING_GOALS',
  'TOPIC_OTHER',
  'FOCUS_PICKER',
  'PROFILE_SUMMARY',
  'COUNCIL_INTRODUCTION',
  'COMPLETE',
]

function nextStepAfter(current: OnboardingStep): OnboardingStep {
  const idx = STEP_ORDER.indexOf(current)
  if (idx === -1 || idx >= STEP_ORDER.length - 1) return current
  return STEP_ORDER[idx + 1]
}

// --- State ---

export interface OnboardingState {
  step: OnboardingStep
  profileId: number | null
  extractedData: Record<string, unknown>
  goals: GoalData[]
  agentMessages: AgentMessage[]
  topicsCompleted: string[]
  isLoading: boolean
  error: string | null
}

const initialState: OnboardingState = {
  step: 'NOT_STARTED',
  profileId: null,
  extractedData: {},
  goals: [],
  agentMessages: [],
  topicsCompleted: [],
  isLoading: false,
  error: null,
}

// --- Actions ---

type OnboardingAction =
  | { type: 'START'; profileId: number }
  | { type: 'NEXT_STEP' }
  | { type: 'SET_EXTRACTED_DATA'; topic: string; data: Record<string, unknown> }
  | { type: 'SET_GOALS'; goals: GoalData[] }
  | { type: 'ADD_GOALS'; goals: GoalData[] }
  | { type: 'UPDATE_GOAL'; index: number; goal: GoalData }
  | { type: 'REMOVE_GOAL'; index: number }
  | { type: 'SET_FOCUS_GOALS'; indices: number[] }
  | { type: 'MARK_TOPIC_COMPLETED'; topic: string }
  | { type: 'SET_AGENT_MESSAGES'; messages: AgentMessage[] }
  | { type: 'SET_LOADING'; loading: boolean }
  | { type: 'SET_ERROR'; error: string | null }
  | { type: 'SKIP_STEP' }

// --- Reducer ---

function onboardingReducer(
  state: OnboardingState,
  action: OnboardingAction,
): OnboardingState {
  switch (action.type) {
    case 'START':
      return {
        ...state,
        profileId: action.profileId,
        step: 'WELCOME',
        error: null,
      }

    case 'NEXT_STEP':
      return {
        ...state,
        step: nextStepAfter(state.step),
        error: null,
      }

    case 'SET_EXTRACTED_DATA':
      return {
        ...state,
        extractedData: {
          ...state.extractedData,
          [action.topic]: action.data,
        },
      }

    case 'SET_GOALS':
      return { ...state, goals: action.goals }

    case 'ADD_GOALS':
      return { ...state, goals: [...state.goals, ...action.goals] }

    case 'UPDATE_GOAL':
      return {
        ...state,
        goals: state.goals.map((g, i) =>
          i === action.index ? action.goal : g,
        ),
      }

    case 'REMOVE_GOAL':
      return {
        ...state,
        goals: state.goals.filter((_, i) => i !== action.index),
      }

    case 'SET_FOCUS_GOALS':
      return {
        ...state,
        goals: state.goals.map((g, i) => ({
          ...g,
          priority: action.indices.includes(i) ? 'focus' : g.priority,
        })),
      }

    case 'MARK_TOPIC_COMPLETED':
      return {
        ...state,
        topicsCompleted: state.topicsCompleted.includes(action.topic)
          ? state.topicsCompleted
          : [...state.topicsCompleted, action.topic],
      }

    case 'SET_AGENT_MESSAGES':
      return { ...state, agentMessages: action.messages }

    case 'SET_LOADING':
      return { ...state, isLoading: action.loading }

    case 'SET_ERROR':
      return { ...state, error: action.error, isLoading: false }

    case 'SKIP_STEP':
      // TOPIC_OTHER is skippable — jump straight to FOCUS_PICKER
      if (state.step === 'TOPIC_OTHER') {
        return { ...state, step: 'FOCUS_PICKER', error: null }
      }
      return { ...state, step: nextStepAfter(state.step), error: null }

    default:
      return state
  }
}

// --- Hook ---

export function useOnboarding() {
  const [state, dispatch] = useReducer(onboardingReducer, initialState)

  const startOnboarding = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', loading: true })
    dispatch({ type: 'SET_ERROR', error: null })
    try {
      const res = await fetch(`${API_URL}/onboarding/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to start onboarding (${res.status})`)
      }
      const data = await res.json()
      dispatch({ type: 'START', profileId: data.profile_id })
    } catch (err) {
      dispatch({
        type: 'SET_ERROR',
        error: err instanceof Error ? err.message : 'Failed to start onboarding',
      })
    } finally {
      dispatch({ type: 'SET_LOADING', loading: false })
    }
  }, [])

  const submitTopicResponse = useCallback(
    async (topic: string, rawInput: string): Promise<Record<string, unknown>> => {
      dispatch({ type: 'SET_LOADING', loading: true })
      dispatch({ type: 'SET_ERROR', error: null })
      try {
        const res = await fetch(`${API_URL}/onboarding/extract`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic, raw_input: rawInput }),
        })
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body.detail || `Extraction failed (${res.status})`)
        }
        const json = await res.json()
        const extracted: Record<string, unknown> = json.extracted_data ?? json
        dispatch({ type: 'SET_EXTRACTED_DATA', topic, data: extracted })
        return extracted
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Failed to extract topic data'
        dispatch({ type: 'SET_ERROR', error: message })
        return {}
      } finally {
        dispatch({ type: 'SET_LOADING', loading: false })
      }
    },
    [],
  )

  const confirmTopic = useCallback(
    async (
      topic: string,
      extractedData: Record<string, unknown>,
      goals?: GoalData[],
    ) => {
      dispatch({ type: 'SET_LOADING', loading: true })
      dispatch({ type: 'SET_ERROR', error: null })
      try {
        const res = await fetch(`${API_URL}/onboarding/confirm-topic`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic,
            extracted_data: extractedData,
            goals: goals ?? [],
          }),
        })
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body.detail || `Failed to confirm topic (${res.status})`)
        }
        dispatch({ type: 'MARK_TOPIC_COMPLETED', topic })
        if (goals && goals.length > 0) {
          dispatch({ type: 'ADD_GOALS', goals })
        }
        dispatch({ type: 'NEXT_STEP' })
      } catch (err) {
        dispatch({
          type: 'SET_ERROR',
          error: err instanceof Error ? err.message : 'Failed to confirm topic',
        })
      } finally {
        dispatch({ type: 'SET_LOADING', loading: false })
      }
    },
    [],
  )

  const completeOnboarding = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', loading: true })
    dispatch({ type: 'SET_ERROR', error: null })
    try {
      const res = await fetch(`${API_URL}/onboarding/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_id: state.profileId }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Failed to complete onboarding (${res.status})`)
      }
      const data = await res.json()
      dispatch({
        type: 'SET_AGENT_MESSAGES',
        messages: data.messages ?? [],
      })
      dispatch({ type: 'NEXT_STEP' })
    } catch (err) {
      dispatch({
        type: 'SET_ERROR',
        error:
          err instanceof Error ? err.message : 'Failed to complete onboarding',
      })
    } finally {
      dispatch({ type: 'SET_LOADING', loading: false })
    }
  }, [state.profileId])

  const nextStep = useCallback(() => {
    dispatch({ type: 'NEXT_STEP' })
  }, [])

  const skipStep = useCallback(() => {
    dispatch({ type: 'SKIP_STEP' })
  }, [])

  const addGoals = useCallback((goals: GoalData[]) => {
    dispatch({ type: 'ADD_GOALS', goals })
  }, [])

  const updateGoal = useCallback((index: number, goal: GoalData) => {
    dispatch({ type: 'UPDATE_GOAL', index, goal })
  }, [])

  const removeGoal = useCallback((index: number) => {
    dispatch({ type: 'REMOVE_GOAL', index })
  }, [])

  const setFocusGoals = useCallback((indices: number[]) => {
    dispatch({ type: 'SET_FOCUS_GOALS', indices })
  }, [])

  return {
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
  }
}
