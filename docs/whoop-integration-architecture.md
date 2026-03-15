# Whoop API Integration Architecture

**Date:** 2026-03-15
**Status:** Design sketch — to be implemented as sub-project 6
**Depends on:** Database models from sub-project 1, Dashboard (sub-project 3), Check-in pre-population (sub-project 4)

---

## Overview

The Whoop integration provides the objective physiological data layer that the Council needs to give recovery-aware, data-informed advice. Rex uses recovery scores to adjust training intensity. Sage uses sleep quality and HRV trends to assess stress. Pattern detection uses Whoop data for cross-domain correlation analysis.

Aura uses the **Whoop v2 API** with OAuth 2.0 authentication. Since Aura is a single-user app, the integration is simpler than a multi-user platform — one set of tokens, one user's data.

---

## What We Need from Whoop

### Core Data (Phase 1)

| Data | API Endpoint | Used By | Frequency |
|---|---|---|---|
| **Recovery score** | `GET /v2/recovery` | Rex (training intensity), dashboard, check-in pre-populate | Daily |
| **HRV (rmssd)** | `GET /v2/recovery` (nested in score) | Rex, Sage, pattern detection | Daily |
| **Resting heart rate** | `GET /v2/recovery` (nested in score) | Pattern detection, trend analysis | Daily |
| **Sleep performance %** | `GET /v2/activity/sleep` | Dashboard, check-in pre-populate, Sage | Daily |
| **Sleep duration** | `GET /v2/activity/sleep` (stage_summary) | Check-in pre-populate, Sage | Daily |
| **Sleep stages** | `GET /v2/activity/sleep` (stage_summary) | Deep analysis, weekly review | Daily |
| **Day strain** | `GET /v2/cycle` (score.strain) | Rex, PM check-in pre-populate | Daily |
| **Workout strain** | `GET /v2/activity/workout` | Rex, workout logging enrichment | Per workout |

### Additional Data (Phase 2+)

| Data | API Endpoint | Used By |
|---|---|---|
| SpO2 percentage | Recovery endpoint | Dr. Vera (health monitoring) |
| Skin temperature | Recovery endpoint | Dr. Vera, Celeste (inflammation correlation) |
| Respiratory rate | Sleep endpoint | Dr. Vera |
| Sleep consistency % | Sleep endpoint | Sage (routine stability) |
| Sleep efficiency % | Sleep endpoint | Sage |
| Workout heart rate zones | Workout endpoint | Rex (training zone analysis) |

---

## OAuth 2.0 Flow

### Scopes Required

```
read:recovery         — Recovery score, HRV, resting heart rate, SpO2, skin temp
read:sleep            — Sleep performance, duration, stages, respiratory rate
read:cycles           — Day strain, average heart rate
read:workout          — Workout strain, heart rate, zones
read:body_measurement — Height, weight, max heart rate
read:profile          — Name, email (for verification only)
```

Request all scopes upfront. Users grant permission once via the Whoop OAuth consent screen.

### Flow

```
1. User taps "Connect Whoop" on dashboard/settings
2. Frontend redirects to Whoop authorization URL:
   https://api.prod.whoop.com/oauth/oauth2/auth
   ?client_id={CLIENT_ID}
   &redirect_uri={REDIRECT_URI}
   &response_type=code
   &scope=read:recovery read:sleep read:cycles read:workout read:body_measurement read:profile
   &state={CSRF_TOKEN}

3. User authenticates with Whoop and grants consent
4. Whoop redirects to our callback URL with an authorization code:
   {REDIRECT_URI}?code={AUTH_CODE}&state={CSRF_TOKEN}

5. Backend exchanges the code for access + refresh tokens:
   POST https://api.prod.whoop.com/oauth/oauth2/token
   Body: {
     grant_type: "authorization_code",
     code: {AUTH_CODE},
     client_id: {CLIENT_ID},
     client_secret: {CLIENT_SECRET},
     redirect_uri: {REDIRECT_URI}
   }

6. Store tokens securely. Access token expires hourly; refresh before use.

7. Trigger initial data backfill (last 30 days).
```

### Token Management

- Access tokens expire after ~1 hour
- Always refresh before making API calls (check expiry timestamp)
- Store refresh token securely (encrypted at rest in Phase 2+, plain in SQLite for Phase 1)
- If refresh fails (user revoked access), mark integration as disconnected and surface a "Reconnect Whoop" card on the dashboard

### Token Storage Model

```
WhoopToken
  id                Integer PK
  user_id           Integer FK → User.id
  access_token      Text
  refresh_token     Text
  token_type        String — "bearer"
  expires_at        DateTime — when the access token expires
  scope             String — granted scopes
  created_at        DateTime
  updated_at        DateTime
  status            Enum: active | expired | revoked
```

---

## Data Sync Strategy

### Daily Sync (Primary)

A scheduled job runs once per day (early morning, after Whoop processes overnight data — **6:00 AM Perth time**). It fetches:

1. **Latest recovery** — `GET /v2/recovery?limit=1` → recovery score, HRV, resting heart rate
2. **Latest sleep** — `GET /v2/activity/sleep?limit=1` → sleep performance, duration, stages
3. **Previous day's cycle** — `GET /v2/cycle?limit=1` → day strain
4. **Previous day's workouts** — `GET /v2/activity/workout?start={yesterday}&end={today}` → workout strain data

All data is stored in the `WhoopSnapshot` model (one record per day) and enriched `WhoopSleep` / `WhoopWorkout` models for detailed data.

### On-Demand Sync

When the morning check-in pre-populate endpoint is called and today's Whoop data doesn't exist yet, trigger a sync before returning. This handles cases where the scheduled sync hasn't run yet or Whoop data was delayed.

```python
async def get_whoop_for_checkin_prepopulate(date, db):
    snapshot = db.query(WhoopSnapshot).filter_by(date=date).first()
    if not snapshot:
        # Trigger on-demand sync
        snapshot = await sync_whoop_data(date, db)
    return snapshot
```

### Initial Backfill

On first connection (after OAuth completes), fetch the last 30 days of data to populate trend charts and give agents historical context. This runs once and uses pagination:

```python
async def backfill_whoop_data(db, days=30):
    start = (date.today() - timedelta(days=days)).isoformat() + "T00:00:00Z"
    # Fetch recovery, sleep, cycles, workouts with start parameter
    # Paginate using nextToken until all records are retrieved
    # Store each day's data as a WhoopSnapshot + detail records
```

### Webhook Support (Phase 2+)

Whoop supports webhooks for real-time data updates. For Phase 1, polling/scheduled sync is sufficient. Phase 2 can add webhook handlers for immediate data availability:

- `recovery.updated` → refresh today's recovery data
- `sleep.updated` → refresh today's sleep data
- `workout.updated` → add/update workout data

---

## Data Models

### WhoopSnapshot (one per day — the summary view)

This is what the dashboard and check-in pre-populate read from. One record per day.

```
WhoopSnapshot
  id                      Integer PK
  date                    Date, unique
  
  # Recovery
  recovery_score          Integer, nullable — 0-100%
  hrv_rmssd_milli         Float, nullable — HRV in milliseconds
  resting_heart_rate      Integer, nullable — bpm
  spo2_percentage         Float, nullable
  skin_temp_celsius       Float, nullable
  
  # Sleep (summarised from detailed sleep record)
  sleep_performance       Integer, nullable — 0-100%
  sleep_duration_milli    Integer, nullable — total sleep time in ms
  sleep_efficiency        Float, nullable — percentage
  sleep_consistency       Integer, nullable — 0-100%
  time_in_bed_milli       Integer, nullable
  disturbance_count       Integer, nullable
  respiratory_rate        Float, nullable
  
  # Day strain (from cycle)
  day_strain              Float, nullable — 0-21 scale
  day_avg_heart_rate      Integer, nullable
  day_max_heart_rate      Integer, nullable
  day_kilojoules          Float, nullable
  
  # Metadata
  score_state             String — "SCORED" | "PENDING_SCORE" | "UNSCORABLE"
  cycle_id                Integer, nullable — Whoop cycle ID for reference
  sleep_id                String, nullable — Whoop sleep UUID
  synced_at               DateTime — when this data was last fetched
  created_at              DateTime
```

### WhoopSleep (detailed, one per sleep event including naps)

```
WhoopSleep
  id                              Integer PK
  whoop_sleep_id                  String, unique — Whoop UUID
  date                            Date
  is_nap                          Boolean
  start                           DateTime
  end                             DateTime
  
  # Stage breakdown (all in milliseconds)
  total_in_bed_milli              Integer, nullable
  total_awake_milli               Integer, nullable
  total_light_sleep_milli         Integer, nullable
  total_slow_wave_sleep_milli     Integer, nullable
  total_rem_sleep_milli           Integer, nullable
  sleep_cycle_count               Integer, nullable
  disturbance_count               Integer, nullable
  
  # Computed
  sleep_performance_percentage    Float, nullable
  sleep_efficiency_percentage     Float, nullable
  sleep_consistency_percentage    Float, nullable
  respiratory_rate                Float, nullable
  
  # Sleep need
  sleep_need_baseline_milli       Integer, nullable
  sleep_need_debt_milli           Integer, nullable
  sleep_need_strain_milli         Integer, nullable
  
  synced_at                       DateTime
```

### WhoopWorkout (one per workout)

```
WhoopWorkout
  id                      Integer PK
  whoop_workout_id        String, unique — Whoop UUID
  date                    Date
  sport_id                Integer
  sport_name              String
  start                   DateTime
  end                     DateTime
  
  # Scores
  strain                  Float, nullable
  average_heart_rate      Integer, nullable
  max_heart_rate          Integer, nullable
  kilojoules              Float, nullable
  distance_meter          Float, nullable
  
  # Heart rate zones (milliseconds in each zone)
  zone_zero_milli         Integer, nullable
  zone_one_milli          Integer, nullable
  zone_two_milli          Integer, nullable
  zone_three_milli        Integer, nullable
  zone_four_milli         Integer, nullable
  zone_five_milli         Integer, nullable
  
  synced_at               DateTime
```

---

## Whoop Service Layer

```python
# backend/integrations/whoop.py

class WhoopService:
    """
    Handles all Whoop API communication.
    Manages token refresh, data fetching, and local storage.
    """
    
    BASE_URL = "https://api.prod.whoop.com/developer"
    TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
    AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
    
    def __init__(self, db_session):
        self.db = db_session
    
    # --- Token Management ---
    
    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if expired."""
        # Load token from DB
        # If expires_at < now + 5 minutes: refresh
        # Return access_token
    
    async def refresh_token(self, token_record) -> None:
        """Exchange refresh token for a new access token."""
        # POST to TOKEN_URL with grant_type=refresh_token
        # Update token record in DB
        # If refresh fails → mark status as expired
    
    async def exchange_code(self, auth_code: str) -> dict:
        """Exchange authorization code for tokens (OAuth callback)."""
        # POST to TOKEN_URL with grant_type=authorization_code
        # Store new WhoopToken record
        # Trigger initial backfill
    
    # --- Data Fetching ---
    
    async def fetch_recovery(self, start: str = None, limit: int = 1) -> list:
        """Fetch recovery data from Whoop API."""
        # GET /v2/recovery with params
        # Handle pagination via nextToken
    
    async def fetch_sleep(self, start: str = None, limit: int = 1) -> list:
        """Fetch sleep data from Whoop API."""
        # GET /v2/activity/sleep with params
    
    async def fetch_cycles(self, start: str = None, limit: int = 1) -> list:
        """Fetch cycle data (day strain) from Whoop API."""
        # GET /v2/cycle with params
    
    async def fetch_workouts(self, start: str = None, end: str = None) -> list:
        """Fetch workout data from Whoop API."""
        # GET /v2/activity/workout with params
    
    # --- Sync Operations ---
    
    async def sync_daily(self, target_date: date) -> WhoopSnapshot:
        """
        Fetch all data for a specific date and upsert into local DB.
        Called by the daily scheduler and on-demand from check-in pre-populate.
        """
        token = await self.get_valid_token()
        
        # Fetch recovery (most recent)
        recovery_data = await self.fetch_recovery(limit=1)
        
        # Fetch sleep (most recent, exclude naps)
        sleep_data = await self.fetch_sleep(limit=1)
        
        # Fetch cycle (most recent)
        cycle_data = await self.fetch_cycles(limit=1)
        
        # Fetch workouts for this date
        workouts = await self.fetch_workouts(
            start=target_date.isoformat() + "T00:00:00Z",
            end=(target_date + timedelta(days=1)).isoformat() + "T00:00:00Z",
        )
        
        # Upsert WhoopSnapshot
        snapshot = self._upsert_snapshot(target_date, recovery_data, sleep_data, cycle_data)
        
        # Upsert detailed records
        self._upsert_sleep_records(sleep_data)
        self._upsert_workout_records(workouts)
        
        self.db.commit()
        return snapshot
    
    async def backfill(self, days: int = 30) -> int:
        """
        Fetch historical data for the last N days.
        Called once after initial OAuth connection.
        Returns the number of snapshots created.
        """
        count = 0
        start_date = date.today() - timedelta(days=days)
        
        # Use pagination to fetch all records in the range
        # Recovery, sleep, cycles all support start/end params
        # Workouts can be fetched in bulk with date range
        
        # For each day, create/update a WhoopSnapshot
        # Store detailed sleep and workout records
        
        return count
    
    # --- Helpers ---
    
    def _upsert_snapshot(self, target_date, recovery, sleep, cycle) -> WhoopSnapshot:
        """Create or update a WhoopSnapshot for the given date."""
        # Check if snapshot exists for this date
        # If yes, update fields. If no, create new.
        # Map API response fields to model fields.
        pass
    
    def _api_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Make an authenticated request to the Whoop API."""
        # Add Authorization: Bearer {token} header
        # Handle rate limiting (429) with exponential backoff
        # Handle 401 by refreshing token and retrying once
        # Raise on other errors
        pass
```

---

## API Endpoints (Aura's Backend)

### OAuth Flow

```
GET /whoop/auth
  → Returns the Whoop authorization URL for the frontend to redirect to

GET /whoop/callback?code={code}&state={state}
  → Handles the OAuth callback, exchanges code for tokens
  → Triggers initial backfill
  → Redirects to dashboard with success message

DELETE /whoop/disconnect
  → Revokes Whoop access, marks token as revoked
  → Clears the "connected" state
```

### Data Access

```
GET /whoop/snapshot/today
  → Returns today's WhoopSnapshot (syncs on-demand if not available)

GET /whoop/snapshot/{date}
  → Returns WhoopSnapshot for a specific date

GET /whoop/snapshots?days=7
  → Returns last N days of snapshots (for trend charts)

GET /whoop/status
  → Returns connection status: { connected: bool, last_synced: datetime, token_status: str }
```

### Manual Sync

```
POST /whoop/sync
  → Triggers an on-demand sync for today's data
  → Returns the updated WhoopSnapshot
```

---

## Error Handling

### Token Expiry / Revocation
If the access token refresh fails (Whoop returns 401 on refresh), mark the integration as disconnected and surface a dashboard card: "Whoop connection lost. Reconnect to keep your data flowing."

### Rate Limiting
The Whoop API returns 429 when rate limited. Implement exponential backoff:
- First retry: 1 second
- Second retry: 2 seconds
- Third retry: 4 seconds
- After 3 failures: log the error, skip this sync, try again next scheduled run

### Missing Data
Whoop sometimes returns `score_state: "PENDING_SCORE"` or `"UNSCORABLE"`. Handle gracefully:
- **PENDING_SCORE:** Store what's available, set a flag to re-fetch in 1 hour
- **UNSCORABLE:** Store null values, don't surface on dashboard (just show "No data")

### Network Failures
If the Whoop API is unreachable during a scheduled sync, log the error and retry at the next scheduled run. Don't surface errors to the user unless the connection is broken for 24+ hours.

---

## Derived Metrics

Some useful values aren't directly in the API but can be calculated:

```python
def compute_sleep_hours(sleep_duration_milli: int) -> float:
    """Convert milliseconds to hours."""
    return round(sleep_duration_milli / 3_600_000, 1)

def compute_sleep_debt(sleep_needed: dict, sleep_duration_milli: int) -> float:
    """How many hours short of need."""
    needed = sleep_needed.get("baseline_milli", 0) + sleep_needed.get("need_from_sleep_debt_milli", 0)
    return round((needed - sleep_duration_milli) / 3_600_000, 1)

def classify_recovery(score: int) -> str:
    """Whoop-style recovery classification."""
    if score >= 67: return "green"    # Good to go
    if score >= 34: return "yellow"   # Use caution
    return "red"                       # Rest recommended

def classify_strain(strain: float) -> str:
    """Classify day strain level."""
    if strain >= 18: return "overreaching"
    if strain >= 14: return "high"
    if strain >= 10: return "moderate"
    return "light"
```

These are used by Rex (recovery classification drives training recommendations) and in the dashboard display.

---

## Integration with Existing Systems

### Check-in Pre-populate
The `GET /checkin/prepopulate/am` endpoint calls `whoop_service.get_snapshot_for_date(today)` to get recovery, HRV, and sleep data. If no snapshot exists, it triggers an on-demand sync.

### Council Round Context
The `assemble_round_context()` function in the Council Round service fetches the last 3–7 days of WhoopSnapshots and includes them in every agent's context.

### Pattern Detection
Several detectors use Whoop data:
- `RecoveryTrendDetector` — declining recovery over 5+ days
- `RecoveryThresholdDetector` — single-day recovery below 30%
- `SleepAnxietyCorrelationDetector` — poor sleep → next-day anxiety
- `StressRecoveryCorrelationDetector` — sustained high anxiety → declining recovery
- `BurnoutRiskDetector` — composite signal including recovery

### Dashboard
The Whoop snapshot block on the dashboard reads from the `WhoopSnapshot` model. Recovery is colour-coded (green/yellow/red). If Whoop isn't connected, the block shows the "Connect Whoop" card from onboarding Layer 3.

---

## Scheduler

```python
# Daily Whoop sync: 6:00 AM Perth time (UTC+8)
# Whoop typically processes overnight data by 5-6 AM
scheduler.add_job(
    daily_whoop_sync,
    CronTrigger(hour=6, minute=0, timezone="Australia/Perth"),
    id="daily_whoop_sync",
    name="Daily Whoop data sync",
)
```

---

## Environment Variables

```
WHOOP_CLIENT_ID        — From Whoop Developer Dashboard
WHOOP_CLIENT_SECRET    — From Whoop Developer Dashboard
WHOOP_REDIRECT_URI     — e.g. http://localhost:8000/whoop/callback (dev)
                         or https://aura.yourdomain.com/whoop/callback (prod)
```

Added to `backend/.env` (gitignored) and documented in `backend/.env.example`.

---

## Security Notes (Phase 1 → Phase 2)

**Phase 1 (local dev):**
- Tokens stored in plaintext in SQLite — acceptable for single-user local app
- WHOOP_CLIENT_SECRET in .env file
- Redirect URI is localhost

**Phase 2 (deployed):**
- Encrypt tokens at rest (Supabase has column-level encryption)
- WHOOP_CLIENT_SECRET in environment variables / secrets manager
- Redirect URI updated to production domain
- HTTPS required for OAuth callback
