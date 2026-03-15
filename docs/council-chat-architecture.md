# Council Chat — Component Architecture

**Date:** 2026-03-15
**Status:** Design sketch — to be implemented in sub-project 5
**Depends on:** Council Round Architecture (backend orchestration), Pattern Detection (proactive messages)

---

## Overview

The Council Chat is a single, unified conversation interface where Shay interacts with the entire Council. It supports two implicit modes — **open floor** (message to the whole Council) and **direct address** (@mention a specific agent) — both using the same round architecture underneath.

The chat timeline renders all Council Round messages chronologically, regardless of trigger: user messages, check-in responses, proactive insights, and scheduled reviews all appear in the same stream.

---

## Design Principles

1. **One interface, not four.** No separate pages per agent in Phase 1. The single chat handles all agent interaction.
2. **Grouped responses, distinct voices.** Agent messages within a round are visually grouped but each agent is clearly identified.
3. **Stream, don't block.** Agent responses appear one at a time as they complete, not all at once after a long wait.
4. **Proactive messages belong in the timeline.** Overnight insights appear as if the agent walked into the room.
5. **Lower the next-message barrier.** Suggestion chips after every round give Shay easy follow-ups.
6. **Agents are present, not hidden.** The presence bar shows who's active and who's currently responding.

---

## Component Hierarchy

```
CouncilChatPage.tsx                — Route: /council. Top-level page.
├── AgentPresenceBar.tsx           — Horizontal strip showing active agent avatars
├── ChatTimeline.tsx               — Scrollable message history
│   ├── DateSeparator.tsx          — "Today", "Yesterday", "March 12"
│   ├── UserMessage.tsx            — Shay's messages (right-aligned)
│   ├── RoundGroup.tsx             — Container for a group of agent responses
│   │   ├── RoundTriggerLabel.tsx  — "After your morning check-in" / "Sage noticed something"
│   │   ├── AgentMessage.tsx       — Individual agent message within a round
│   │   │   ├── AgentAvatar.tsx    — Small circular avatar with agent colour
│   │   │   ├── AgentName.tsx      — Display name + domain tag
│   │   │   └── MessageBody.tsx    — Rendered text content
│   │   └── ConflictIndicator.tsx  — "The Council is split" badge (when agents disagree)
│   ├── ProactiveRoundGroup.tsx    — Variant of RoundGroup for proactive/overnight messages
│   └── SuggestionChips.tsx        — 2-3 tappable follow-up suggestions after a round
├── TypingIndicator.tsx            — "The Council is reviewing..." with animated agent avatars
├── ChatInput.tsx                  — Text input with @mention support
│   ├── MentionAutocomplete.tsx    — Dropdown for @agent selection
│   └── SendButton.tsx             — Submit with loading state
└── ScrollAnchor.tsx               — Invisible element at bottom, auto-scroll target
```

---

## Component Specifications

### CouncilChatPage

Top-level page component. Manages:
- Loading chat history on mount (recent rounds with their messages)
- Sending new messages (triggers a round via API)
- Receiving streaming responses (SSE or polling)
- Auto-scrolling to newest message
- Managing the "responding" state for the typing indicator

```typescript
// Key state
interface ChatPageState {
  rounds: RoundWithMessages[]       // All rounds with their messages
  activeRoundId: number | null      // Currently in-progress round
  respondingAgent: string | null    // Which agent is currently generating
  suggestions: string[]             // Current suggestion chips
  isLoading: boolean                // Initial history load
}
```

### AgentPresenceBar

Horizontal strip at the top of the chat, below the page header.

```
┌──────────────────────────────────────────────────┐
│  (Aurore)  (Rex)  (Sage)  (Celeste)              │
│     ○        ○      ●        ○                   │
└──────────────────────────────────────────────────┘
```

- Small circular avatars for each Phase 1 agent
- **Idle state:** muted opacity, subtle border
- **Responding state (●):** full opacity, gentle pulse animation, agent's accent colour border
- **Mentioned state:** when Shay @mentions an agent, that avatar gets a subtle highlight before the round starts
- Tapping an avatar pre-fills `@agentname ` in the input field (quick @mention shortcut)

### ChatTimeline

Scrollable container holding all messages. Loads the most recent N rounds on mount (paginated — load more on scroll-up).

**Scroll behaviour:**
- Auto-scrolls to bottom on new messages IF the user is already near the bottom (within 100px)
- If the user has scrolled up to read history, do NOT auto-scroll — show a "New messages ↓" pill instead
- On mount, scroll to bottom

**Message ordering:**
- Messages are grouped by round
- Rounds are ordered by `created_at` ascending
- Within a round, messages are ordered by `sequence_order`
- User messages appear above their triggered round
- Proactive rounds (no user message) appear standalone with a contextual label

### UserMessage

Right-aligned message bubble. Shay's messages.

```
                                    ┌─────────────────────┐
                                    │ How should I train   │
                                    │ today? Recovery was  │
                                    │ pretty low.          │
                                    └─────────────────────┘
                                                   2:34 PM
```

- Background: `aura-surface`
- Text: `aura-brown`
- Timestamp: `aura-muted`, small, right-aligned below
- If the message contains an @mention, the agent name is rendered in that agent's accent colour

### RoundGroup

Container for agent responses from a single round. Visually groups them as one conversation beat.

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
  After your morning check-in · 7:52 AM
│                                                   │
  (Rex avatar) Rex
│ Sage is right that today isn't the day to push.   │
  42% recovery and anxiety at 7 — I'm swapping
│ your session to mobility work. 20 minutes,        │
  hips and thoracic spine. Streak stays alive.
│                                                   │
  (Sage avatar) Sage
│ Your anxiety has climbed from 4 to 7 this week.   │
  That's not random. Protect Wednesday evening —
│ it's your rest night. And do a 10-min NSDR        │
  before your study block tonight.
│                                                   │
  (Celeste avatar) Celeste
│ Quick note: broken sleep and cortisol aren't       │
  great for your barrier. Tonight is azelaic —
│ good timing. Extra Vanicream.                      │
│                                                   │
  ┌──────────┐ ┌───────────────┐ ┌────────────┐
│ │ What about│ │ Can I do a    │ │ Tell me    │ │
  │ tomorrow? │ │ light walk?   │ │ more, Sage │
│ └──────────┘ └───────────────┘ └────────────┘ │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

- Light container: no solid border, just a subtle background shift or extra vertical spacing
- **RoundTriggerLabel** at top: contextual label explaining what triggered this round
  - Check-in round: "After your morning check-in · 7:52 AM"
  - Chat round: no label needed (the user message above is the trigger)
  - Proactive round: "Sage noticed something · overnight" or "Council weekly review · Sunday"
- Agent messages stacked vertically within the group, minimal spacing between them
- Suggestion chips at the bottom of the group

### AgentMessage

Individual agent's contribution within a round.

```
(●) Rex                              
Sage is right that today isn't the day to push.
42% recovery and anxiety at 7 — I'm swapping your
session to mobility work. 20 minutes, hips and
thoracic spine. Streak stays alive.
```

- **Avatar:** small circle (24px) with agent's accent colour or initial
- **Name:** agent display name in `font-display` (Cormorant Garamond), agent accent colour
- **Body:** `font-body` (DM Sans), `aura-brown`, normal text rendering
- **Mentions highlighted:** when an agent references another agent by name, that name is rendered in the referenced agent's colour (subtle, not flashy — just a colour change on the name)
- **Streaming state:** text appears word-by-word or sentence-by-sentence as it streams in. Cursor/caret animation at the end while still generating.

### Agent Accent Colours

Each agent gets a subtle accent used for their avatar border, name colour, and mention highlights:

| Agent | Accent | Notes |
|---|---|---|
| Aurore | `aura-gold` | The conductor — gold fits her elevated position |
| Rex | A warm terracotta/rust | Physical, grounded — could be a new token like `aura-rust` |
| Sage | A soft sage green | Obvious but appropriate — could be `aura-sage` |
| Celeste | `aura-blush` | Already in the palette, fits the skincare/self-care domain |

These would be added to `tailwind.config.ts` as new tokens if they don't already exist.

### ConflictIndicator

When the `mentions` analysis detects disagreement between agents in a round:

```
┌──────────────────────────────────────┐
│ ⚖ The Council is split on this      │
│                                      │
│ [Go with Rex's plan] [Go with Sage] │
└──────────────────────────────────────┘
```

- Appears between conflicting agent messages or at the bottom of the round group
- Small, non-intrusive badge
- Optional action buttons if the disagreement is about a concrete recommendation
- Tapping a choice sends a message like "I'll go with Rex's plan" which triggers a brief follow-up round

### ProactiveRoundGroup

Variant of RoundGroup for proactive/overnight messages. Visually distinguished:

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
  ✦ Sage noticed something · overnight
│                                                   │
  (Sage avatar) Sage
│ I've been looking at your data from this week.    │
  Your anxiety has climbed every day since Monday —
│ 4, 5, 5, 6, 7. Combined with your recovery       │
  trending down, I want to flag this before it
│ becomes a bigger pattern.                          │
│                                                   │
  What's driving the stress this week?
│                                                   │
  ┌──────────────┐ ┌────────────────────┐
│ │ Work stuff    │ │ I'm not sure, help │ │
  │               │ │ me figure it out   │
│ └──────────────┘ └────────────────────┘ │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

- ✦ icon or subtle different background to mark it as proactive (not a response to Shay)
- Same internal structure as RoundGroup but with a "noticed something" style trigger label
- These appear in the timeline chronologically — if they were generated overnight, they sit at the top of "Today" when Shay opens the app

### SuggestionChips

2–3 tappable follow-up suggestions generated by Aurore as part of round completion.

```typescript
interface SuggestionChip {
  text: string           // Display text, e.g. "What about tomorrow?"
  targetAgent?: string   // If the chip is directed at a specific agent
}
```

- Rendered as pill-shaped buttons below the last agent message in a round
- `aura-surface` background, `aura-brown` text, `rounded-full`
- On tap: the chip text is sent as a new user message (with optional target_agent)
- Chips disappear once Shay sends any message (whether by tapping a chip or typing)
- On new rounds, previous chips are replaced

**Generation:** Aurore's triage output includes a `suggestions` field:
```json
{
  "agent_order": ["sage", "rex"],
  "flags": ["anxiety_trending_up"],
  "summary": "...",
  "suggestions": [
    {"text": "What about tomorrow?", "target_agent": "rex"},
    {"text": "Tell me more, Sage", "target_agent": "sage"},
    {"text": "What can I do right now?"}
  ]
}
```

### TypingIndicator

Shown while a round is in progress — between the user message being sent and all agent responses completing.

```
┌──────────────────────────────────────┐
│ (●) (○) (○)  The Council is          │
│              reviewing...             │
└──────────────────────────────────────┘
```

- Shows rotating agent avatars or a gentle dot animation
- Updates as each agent completes: once Rex's message appears in the timeline, the indicator shifts to show the next agent
- Disappears when the round is complete

### ChatInput

Text input area at the bottom of the screen (sticky/fixed).

```
┌──────────────────────────────────────────────────┐
│ Message The Council...                     [Send] │
└──────────────────────────────────────────────────┘
```

- Placeholder text rotates contextually:
  - Default: "Message The Council..."
  - After @mention started: "Message Celeste..."
  - Morning, no check-in done: "How are you feeling this morning?"
  - Evening: "How'd today go?"
- **@mention detection:** typing `@` triggers MentionAutocomplete dropdown
- Input grows vertically for multi-line messages (up to 4 lines, then scrolls)
- Send button: disabled when empty, `aura-blush` when active
- Send on Enter (Shift+Enter for newline)

### MentionAutocomplete

Dropdown that appears when `@` is typed in the input.

```
┌──────────────────┐
│ (●) Aurore       │
│ (●) Rex          │
│ (●) Sage         │ ← keyboard navigable, tap/click to select
│ (●) Celeste      │
└──────────────────┘
```

- Filters as user types: `@re` shows only Rex
- Selecting inserts `@Rex ` into the input and sets `targetAgent` state
- Can also be triggered by tapping an avatar in the AgentPresenceBar

---

## Streaming Strategy

### Phase 1 Approach: Polling

Simplest implementation, zero infrastructure overhead:

```
1. POST /council/round/chat  { message, target_agent }
   → Returns { round_id, status: "in_progress" }

2. Poll GET /council/round/{round_id}/messages  every 1 second
   → Returns { status, messages: [...completed so far] }

3. Frontend diffs against what's already rendered
   → New messages get appended to the timeline with a fade-in

4. When status == "complete", stop polling, show suggestion chips
```

### Phase 2 Upgrade: Server-Sent Events (SSE)

More responsive, less wasteful than polling:

```
1. POST /council/round/chat  { message, target_agent }
   → Returns { round_id }

2. Connect to GET /council/round/{round_id}/stream  (EventSource)
   → Server sends events as each agent completes:
     event: agent_message
     data: { agent_name: "rex", message: "...", sequence_order: 1 }

     event: agent_message
     data: { agent_name: "sage", message: "...", sequence_order: 2 }

     event: round_complete
     data: { suggestions: [...] }

3. Frontend renders each message as the event arrives
```

### Phase 3 Upgrade: WebSocket

If real-time features expand (live collaboration, notifications in-app), WebSocket becomes worth the infrastructure. Not needed for Phase 1–2.

### Recommendation
**Start with polling in Phase 1.** It's trivial to implement, works with the existing FastAPI setup, and the user experience is still good (1-second polling means messages appear within a second of being generated). Upgrade to SSE in Phase 2 when the infrastructure justifies it.

---

## API Endpoints (Chat-Specific)

### Send Message
```
POST /council/round/chat
Body: {
  message: string,
  target_agent: string | null
}
Response: {
  round_id: number,
  status: "in_progress"
}
```

### Poll Round Status
```
GET /council/round/{round_id}/messages
Response: {
  round_id: number,
  status: "in_progress" | "complete",
  messages: [
    {
      id: number,
      agent_name: string,
      display_name: string,
      message: string,
      sequence_order: number,
      mentions: string[],
      created_at: string
    }
  ],
  suggestions: [                    // Only present when status == "complete"
    { text: string, target_agent?: string }
  ]
}
```

### Load Chat History
```
GET /council/chat/history?limit=20&before={round_id}
Response: {
  rounds: [
    {
      id: number,
      triggered_by: string,
      created_at: string,
      user_message: string | null,     // null for proactive rounds
      target_agent: string | null,
      messages: [AgentMessage],
      suggestions: [SuggestionChip]    // preserved for context
    }
  ],
  has_more: boolean
}
```

This endpoint returns rounds with their messages pre-joined (not separate calls). Pagination is cursor-based using `before` (the oldest round_id in the current view).

### Resolve Conflict
```
POST /council/round/{round_id}/resolve
Body: {
  chosen_agent: string,
  context: string              // e.g. "I'll go with Rex's plan"
}
```
Stores the preference and optionally triggers a brief follow-up round where the chosen agent confirms and the other acknowledges.

---

## Chat History Loading

### Initial Load
On mount, fetch the most recent 20 rounds. This covers roughly 2–3 days of activity (assuming 3-4 rounds per day from check-ins + proactive + chat).

### Scroll-Up Pagination
When the user scrolls to the top of the timeline, fetch the next 20 rounds using the `before` cursor. Show a small loading spinner at the top during fetch.

### New Round Injection
When a new round is created (user sends a message), it's immediately added to the local state as `in_progress`. Messages are appended as they arrive via polling. No need to re-fetch history.

### Proactive Round Detection
If Shay opens the chat and there are proactive rounds since her last visit, these appear at the top of "today" in the timeline. A subtle "New from the Council" marker highlights them so she knows to scroll up and read.

---

## Responsive Layout

### Desktop (≥768px)
- Full-width within the PageWrapper max-width (1024px)
- AgentPresenceBar spans full width below the page header
- ChatTimeline fills available height (flexbox: flex-1, overflow-y: auto)
- ChatInput fixed to the bottom of the page content area
- Agent messages have comfortable reading width (max ~680px)

### Mobile (<768px)
- Full-width, full-height layout (chat takes over the viewport)
- AgentPresenceBar horizontally scrollable if needed (for Phase 2+ with more agents)
- ChatInput fixed to the bottom of the screen, above the OS keyboard
- Smaller avatars and tighter spacing
- Suggestion chips wrap to multiple rows if needed

---

## TypeScript Interfaces

```typescript
// Core types used across chat components

interface AgentInfo {
  name: string            // "rex", "sage", etc.
  displayName: string     // "Rex", "Sage", etc.
  accentColour: string    // Tailwind class: "text-aura-rust", "text-aura-sage"
  avatarUrl?: string      // Optional image, falls back to initial
}

interface ChatMessage {
  id: number
  agentName: string
  displayName: string
  message: string
  sequenceOrder: number
  mentions: string[]
  createdAt: string
}

interface ChatRound {
  id: number
  triggeredBy: string     // "user_message" | "checkin_am" | "proactive" | etc.
  createdAt: string
  status: "in_progress" | "complete"
  userMessage: string | null
  targetAgent: string | null
  messages: ChatMessage[]
  suggestions: SuggestionChip[]
}

interface SuggestionChip {
  text: string
  targetAgent?: string
}

// Chat page state
interface ChatState {
  rounds: ChatRound[]
  activeRoundId: number | null
  respondingAgent: string | null
  hasMore: boolean         // More history available
  isLoadingHistory: boolean
}

// Input state
interface InputState {
  text: string
  targetAgent: string | null
  isSending: boolean
  showMentionAutocomplete: boolean
}
```

---

## State Management

For Phase 1, React local state (`useState` + `useReducer`) is sufficient. The chat page manages:

```typescript
type ChatAction =
  | { type: 'LOAD_HISTORY'; rounds: ChatRound[]; hasMore: boolean }
  | { type: 'SEND_MESSAGE'; message: string; targetAgent: string | null; roundId: number }
  | { type: 'AGENT_MESSAGE_RECEIVED'; roundId: number; message: ChatMessage }
  | { type: 'ROUND_COMPLETE'; roundId: number; suggestions: SuggestionChip[] }
  | { type: 'CLEAR_SUGGESTIONS' }
```

### Custom Hook: `useCouncilChat`

Encapsulates all chat logic:

```typescript
function useCouncilChat() {
  // Returns:
  return {
    rounds,                    // All loaded rounds
    activeRoundId,             // Currently in-progress round
    respondingAgent,           // Who's currently generating
    suggestions,               // Current suggestion chips
    hasMore,                   // More history available

    sendMessage,               // (text, targetAgent?) => void
    loadMoreHistory,           // () => void
    resolveConflict,           // (roundId, chosenAgent) => void
    tapSuggestion,             // (chip) => void
  }
}
```

### Custom Hook: `useRoundPolling`

Handles the polling logic for an active round:

```typescript
function useRoundPolling(roundId: number | null, onMessage: callback, onComplete: callback) {
  // Polls GET /council/round/{roundId}/messages every 1s
  // Calls onMessage for each new message
  // Calls onComplete when round status == "complete"
  // Cleans up interval on unmount or when roundId changes
}
```

---

## Animation & Transitions

Keep animations subtle and warm — consistent with the Aura brand.

- **New agent message:** fade-in + slight slide-up (200ms ease-out)
- **Suggestion chips:** staggered fade-in after round completes (100ms delay between each)
- **Typing indicator:** gentle pulse animation on agent avatars
- **Presence bar responding state:** subtle pulse on the active agent's avatar border
- **Scroll-to-bottom pill:** fade-in when new messages arrive while scrolled up
- **@mention autocomplete:** slide-down from input (150ms)

No bouncing, no flashing, no attention-grabbing animations. Everything smooth and calm.

---

## Accessibility

- All agent avatars have `alt` text with agent name
- Chat timeline is an ARIA live region (`aria-live="polite"`) so screen readers announce new messages
- @mention autocomplete is keyboard navigable (arrow keys + Enter)
- Suggestion chips are focusable buttons
- Sufficient colour contrast for all agent accent colours against backgrounds
- Timestamps are in `<time>` elements with `datetime` attributes
- Send button has clear disabled/active states
