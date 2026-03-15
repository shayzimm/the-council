export type OnboardingStep =
  | 'NOT_STARTED'
  | 'WELCOME'
  | 'TOPIC_LIFESTYLE'
  | 'TOPIC_LIFESTYLE_GOALS'
  | 'TOPIC_SKIN'
  | 'TOPIC_SKIN_GOALS'
  | 'TOPIC_WELLBEING'
  | 'TOPIC_WELLBEING_GOALS'
  | 'TOPIC_OTHER'
  | 'FOCUS_PICKER'
  | 'PROFILE_SUMMARY'
  | 'COUNCIL_INTRODUCTION'
  | 'COMPLETE'

export interface GoalData {
  id?: number
  title: string
  domain: string
  goal_type: string
  target_value?: number | null
  target_unit?: string | null
  deadline?: string | null
  linked_agent: string
  priority?: string
}

export interface AgentMessage {
  agent_name: string
  display_name: string
  message: string
  accent_color: string
}

export interface ExtractedProfileData {
  [key: string]: unknown
}
