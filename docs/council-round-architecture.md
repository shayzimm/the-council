# Council Round Orchestration Architecture

**Date:** 2026-03-15
**Status:** Design sketch — to be implemented in sub-projects 4–5
**Depends on:** Existing FastAPI + SQLAlchemy + Pydantic v2 stack from sub-project 1

---

## Overview

A **Council Round** is the fundamental unit of agent collaboration. Every meaningful trigger (check-in, chat message, Whoop sync, proactive detection, weekly review) initiates a round — a structured sequence of agent responses that share context and build on each other.

This is what makes the Council feel like a team rather than four separate chatbots.

---

## How a Round Flows

### Step 1 — Context Assembly
Before any agent speaks, the system assembles a shared **context packet** containing:
- The trigger event (check-in data, chat message, Whoop snapshot, etc.)
- Recent history (last 7 days of check-ins, Whoop, streaks, active goals)
- Last N Council messages across all agents
- Any detected patterns from the pattern detection engine

### Step 2 — Aurore Triages
Aurore always goes first. She produces:
- **Internal triage** (not shown to user): which agents should respond, in what order, key flags
- **Optional user-facing message**: greeting, weekly synthesis, or a flag
- **Agent order array**: e.g. `["sage", "rex", "celeste"]`

Triage is returned in `<triage>` XML tags containing JSON, parsed by the service.

### Step 3 — Domain Agents Respond Sequentially
Each agent receives the full context packet PLUS everything said so far in this round (Aurore's triage + prior agent messages). This is what enables genuine cross-talk — Rex can reference Sage's stress flag, Celeste can note what Rex already covered.

### Step 4 — Optional Rebuttal Pass
For high-stakes situations (conflicting recommendations, significant pattern shifts), a second pass lets agents briefly respond to what others said. Gated behind a relevance check to avoid noise.

### Step 5 — Round Stored as a Unit
All messages linked by `council_round_id`, preserving sequence and shared context.

---

## Data Models

### CouncilRound

| Field | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `triggered_by` | Enum | `checkin_am`, `checkin_pm`, `whoop_sync`, `user_message`, `proactive`, `weekly_review` |
| `trigger_reference_id` | Integer FK, nullable | Points to the check-in, message, etc. Null for proactive rounds. |
| `triage_summary` | Text, nullable | Aurore's internal routing notes. Not shown to user. |
| `agent_order` | JSON, nullable | e.g. `["aurore", "rex", "sage"]` — set by Aurore's triage. |
| `status` | Enum | `in_progress`, `complete`, `failed` |
| `created_at` | DateTime | |
| `completed_at` | DateTime, nullable | |

### CouncilMessage (updated from original brief)

| Field | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `round_id` | Integer FK → `council_rounds.id` | |
| `agent_name` | String(50) | |
| `sequence_order` | Integer | 0 = Aurore triage, 1+ = domain agents |
| `message` | Text | User-facing text — what Shay sees |
| `internal_reasoning` | Text, nullable | Agent's chain-of-thought. Not shown to user. Useful for debugging. |
| `mentions` | JSON | List of agent names referenced, e.g. `["sage", "celeste"]` |
| `in_reply_to` | Integer FK → `council_messages.id`, nullable | Explicit response to another agent |
| `visibility` | Enum | `user_facing` or `internal_only` |
| `created_at` | DateTime | |

---

## Agent Registry

Each agent is defined by: `name`, `display_name`, `domain`, `system_prompt`, and `is_conductor` (True only for Aurore).

### Phase 1 Agents
- **Aurore** — conductor, triage, synthesis. Always goes first.
- **Rex** — strength training, body composition, recovery-aware programming
- **Sage** — stress, anxiety, emotional regulation, burnout, NSDR
- **Celeste** — skincare routine, ingredients, lifestyle-skin connections

System prompts explicitly instruct agents to:
- Reference other agents by name when building on or disagreeing with their messages
- Adjust recommendations based on what other agents have flagged
- Keep responses concise (2–4 paragraphs max)
- Not repeat information another agent already covered

---

## Prompt Structure

Each agent's Claude API call receives:

1. **System prompt** — personality, domain, behavioural rules (from agent registry)
2. **User message** — assembled context containing:
   - Raw trigger data (check-in values, chat message, etc.)
   - Recent Whoop data (last 3 days)
   - Recent check-in trends (last 7 days)
   - Active streaks and goals
   - Recent Council messages from prior rounds
   - Aurore's triage summary (for non-Aurore agents)
   - Prior agent messages in THIS round (accumulated context)
   - Detected patterns from pattern detection engine
   - Task instruction ("Respond to Shay as [agent]. Reference other agents if relevant.")

---

## Agent Ordering Strategy

Aurore's triage dynamically determines agent order based on the data:
- If recovery is tanked → Rex leads
- If anxiety is spiking → Sage leads
- If it's a tret night and skincare was skipped → Celeste leads
- The "primary" agent sets the tone; subsequent agents respond in that context

---

## Conflict Handling

Agents can and should disagree. When the `mentions` field indicates disagreement:
- UI shows a "Council is split" indicator
- User can "cast a deciding vote" — choose which advice to follow
- Decision stored as preference data, fed back into future triage

---

## API Integration

### Post-Check-in Round
```
POST /council/round/checkin
Body: { checkin_type: "am" | "pm", checkin_id: int }
```
Called by the check-in confirm endpoint after data is saved.

### User Chat Round
```
POST /council/round/chat
Body: { message: str, target_agent: str | null }
```
Called when Shay sends a message in the Council Chat. `target_agent` supports @mention routing.

---

## Example Flow: Morning Check-in

Shay submits: Energy 5, Mood 6, Anxiety 7, Sleep "Restless, woke up twice", Intention "Get through the day without overcommitting"

1. **Context assembled** — today's check-in + 5-day anxiety trend (4→5→5→6→7) + Whoop recovery 42%
2. **Aurore triages** — anxiety trending up, recovery low, overcommit pattern detected. Orders: Sage → Rex → Celeste.
3. **Sage responds** — flags the 5-day anxiety trend, prescribes NSDR, tells Shay to protect Wednesday evening
4. **Rex responds** — references Sage's stress flag, pulls back to mobility only, confirms streak stays alive
5. **Celeste responds** — notes sleep-skin impact briefly, confirms tonight's azelaic is gentler, defers to Sage and Rex on the rest

Result: Shay sees three coordinated responses from agents who clearly talked to each other.
