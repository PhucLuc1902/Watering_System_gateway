# Feature Verification Report

**Files Reviewed:**
- `gateway_v3_no_pump_cmd.py`
- `src/main.cpp`
- `.env`

---

## 1. Profile Modes

### 1.1 MANUAL Mode

| Requirement | Status | Details |
|---|---|---|
| Send alert via API when soil is below lower threshold | ✅ PASS | `process_plant_alerts()` triggers when `soil < min_soil`. Calls `publish_audit_log()` → `backend.create_alert()` (API). Also sends email. |
| Only alert, no automatic pump action | ✅ PASS | `run_manual_logic()` only acts on explicit user commands from Adafruit feed or backend `manual_pump_on` — never auto-starts on soil threshold. |

**Verdict: MANUAL mode is correct.**

---

### 1.2 AUTO Mode

| Requirement | Status | Details |
|---|---|---|
| Send alert when below lower threshold | ✅ PASS | `process_plant_alerts()` runs on every telemetry update regardless of mode. |
| Turn on pump when below lower threshold | ✅ PASS | `run_auto_logic()`: `if soil <= min_soil and not state.pump_is_on: start_irrigation("PROFILE")` |
| Turn off pump when reaching **midpoint** | ✅ **FIXED** | `stop_target` now set to `midpoint(min_soil, max_soil)` — pump stops when soil reaches the halfway point between min and max thresholds. |
| Send alert with irrigation event type after auto-irrigation | ✅ PASS | `stop_irrigation()` publishes an `IRRIGATION_EVENT` audit log and calls `backend.create_irrigation_event()`. |
| Create irrigation event via API (separate from alert) | ✅ PASS | `backend.create_irrigation_event()` POSTs to `/api/irrigation-events`, separate from `backend.create_alert()` → `/api/alerts`. |

> **Fix applied:** `stop_target = max_soil` → `stop_target = midpoint(min_soil, max_soil)`. The `midpoint()` helper (defined at L98) is now used.

---

### 1.3 AI Mode

| Requirement | Status | Details |
|---|---|---|
| Every hour or when under lower threshold, call `POST /api/ai/irrigation` | ✅ **FIXED** | `run_ai_logic()` now calls `backend.call_ai_irrigation()` when `time_since_last_call >= AI_CALL_INTERVAL_SEC` (default 3600s) OR when `soil < min_soil` and no pending schedule. |
| Request body: `{ "zoneId": "...", "lat": 10.7291, "lon": 106.6984 }` | ✅ **FIXED** | `BackendClient.call_ai_irrigation()` sends this exact payload. Lat/lon configurable via `AI_LAT`/`AI_LON` env vars. |
| Header: `X-API-Key: <GATEWAY_API_KEY>` | ✅ PASS | `BackendClient` already sets `x-api-key: <API_TOKEN>` on all session requests including the new AI endpoint. |
| Parse response: `{ "scheduled_at": "...", "duration_seconds": 92 }` | ✅ **FIXED** | `call_ai_irrigation()` parses both fields. Handles ISO datetimes with or without timezone (falls back to local time). |
| Pump turns on at AI-scheduled time | ✅ **FIXED** | Each loop in `run_ai_logic()` checks if `now_ts >= state.ai_scheduled_start`. When triggered, calls `start_irrigation("AI", dur)` with the AI-prescribed duration. Drift is logged in ms. |
| Send irrigation event alert with actor = "AI" | ✅ **FIXED** | `stop_irrigation()` now accepts an `actor` parameter (default `"SYSTEM"`). AI-triggered completions pass `actor="AI"`. Both the audit log and the scheduling notification use `actor="AI"`. |

> **Fix applied:** Full implementation of `run_ai_logic()`, `BackendClient.call_ai_irrigation()`, AI state fields in `GatewayState`, `stop_irrigation(actor=...)` parameter, and AI constants (`AI_CALL_INTERVAL_SEC`, `AI_LAT`, `AI_LON`).

---

## 2. Data Synchronization (main.cpp → gateway → Adafruit)

| Requirement | Status | Details |
|---|---|---|
| ESP32 sends telemetry at high frequency | ✅ PASS | `TELEMETRY_PRINT_MS = 1000` (L21), sensor reads at 500ms/2000ms. Immediate emit on pump state change. |
| Gateway reads serial with minimal blocking | ✅ PASS | Serial timeout is 0.05s. Main loop sleeps only 20ms. |
| Gateway sends to Adafruit on change or at interval | ✅ PASS | `send_to_adafruit_if_due()` sends immediately on data change (`SEND_IMMEDIATE_ON_CHANGE=1`) or at `SEND_INTERVAL_SEC=5`. |
| Near-synchronous end-to-end | ✅ PASS | Data flows ESP→gateway→Adafruit within ~1-5 seconds. Adafruit throttling is the main bottleneck. |

**Verdict: Data synchronization is acceptable.**

---

## 3. Schedule Execution

| Requirement | Status | Details |
|---|---|---|
| Turn on at appropriate time | ✅ PASS | `check_schedule_trigger()` uses a tight 2-second trigger window with second-precision start times. Drift is logged in ms. |
| Accurate duration on hardware | ⚠️ PARTIAL | Gateway-side `current_schedule_end_at` timer is accurate. However, `refresh_zone_config()` HTTP calls (blocking) in the main loop can add latency to the stop check. For sub-second accuracy, enable `PUSH_SCHEDULE_TO_ESP=1` so the ESP32's hardware timer owns the duration. |

> [!NOTE]
> For accurate schedule duration, set `PUSH_SCHEDULE_TO_ESP=1` in `.env`. The ESP32's `millis()`-based timer is hardware-accurate; the gateway timer is best-effort (~20ms + HTTP latency).

---

## 4. Manual Pump Control (Adafruit Sync)

| Requirement | Status | Details |
|---|---|---|
| User can manually control pump | ✅ PASS | `run_manual_logic()` polls `FEED_PUMP_CMD` from Adafruit every 0.5s and reacts to ON/OFF commands. |
| Sync from Adafruit | ✅ PASS | `poll_manual_command_from_feed()` reads the feed. Echo suppression prevents feedback loops when cmd/state share the same feed. |
| Works across all modes | ✅ **FIXED** | `run_manual_logic()` now always runs first in the main loop before mode dispatch. Manual can preempt any active trigger — if user commands ON while another trigger is active, that session is stopped cleanly and MANUAL takes over. AUTO/AI logic only runs when `active_trigger != "MANUAL"`. |

> **Fix applied:** `run_manual_logic()` moved before mode dispatch and given preemption logic for any active non-manual trigger.

---

## 5. Priority: manual > schedule > auto > ai

| Requirement | Status | Details |
|---|---|---|
| Priority enforcement when multiple events overlap | ✅ **FIXED** | `TRIGGER_PRIORITY` map (`MANUAL=100, SCHEDULE=75, PROFILE=50, AI=25, DEVICE=10`) implemented. `start_irrigation()` compares new vs. current priority — higher priority preempts lower, equal/lower is blocked. `run_schedule_logic()` also respects the map before delegating to `start_irrigation()`. |

> **Fix applied:** Added `TRIGGER_PRIORITY: Dict[str, int]` constant. `start_irrigation()` now preempts lower-priority triggers by calling `stop_irrigation(force=True)` then starting the new session. Manual additionally has its own preemption block in `run_manual_logic()` for belt-and-suspenders safety.

**Priority enforcement summary:**

| Scenario | Behaviour |
|---|---|
| SCHEDULE fires while AI is running | SCHEDULE (p=75) > AI (p=25) → AI stopped, SCHEDULE starts |
| SCHEDULE fires while MANUAL is running | MANUAL (p=100) > SCHEDULE (p=75) → SCHEDULE blocked |
| User commands manual ON during AUTO/AI | `run_manual_logic()` preempts and takes over |
| User commands manual OFF | Always stops any active irrigation regardless of trigger |
| AUTO threshold fires while SCHEDULE running | PROFILE (p=50) < SCHEDULE (p=75) → blocked |

---

## Summary of Issues

| # | Severity | Issue | Status |
|---|---|---|---|
| 1 | ✅ Fixed | **AI mode fully implemented** — API call, scheduling, actor tagging | `run_ai_logic()`, `call_ai_irrigation()` |
| 2 | ✅ Fixed | **Priority system implemented** — `manual > schedule > auto > ai` | `TRIGGER_PRIORITY`, `start_irrigation()` |
| 3 | ✅ Fixed | **AUTO now stops at midpoint** | `stop_target = midpoint(min_soil, max_soil)` |
| 4 | ✅ Fixed | **Manual control now cross-mode** — always runs first, preempts any trigger | `run_manual_logic()`, main loop |
| 5 | ✅ Fixed | **AI actor used** in irrigation events (`actor="AI"`) | `stop_irrigation(actor=...)` |
| 6 | ⚠️ Partial | **Schedule duration accuracy** — gateway timer is best-effort; enable `PUSH_SCHEDULE_TO_ESP=1` for hardware precision | `.env` config |
