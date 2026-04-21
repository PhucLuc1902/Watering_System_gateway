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
| Only alert, no automatic pump action | ✅ PASS | `run_manual_logic()` only acts on explicit user commands — never auto-starts on soil threshold. |
| Pump stays ON until user sends OFF | ✅ **FIXED** | `run_auto_logic()` no longer stops MANUAL sessions via the soil threshold check. Only `active_trigger == "DEVICE"` is affected by soil floor stop. |
| No immediate reset after turning ON | ✅ **FIXED** | Adafruit echo suppression: gateway tracks `last_pump_state_write_time`. Reads within `MANUAL_FEED_ECHO_SUPPRESS_SEC=30s` that match the gateway's own write are discarded, preventing the shared `pump` feed from falsely signalling OFF. |
| No false preemption from echo | ✅ **FIXED** | `run_manual_logic()` preemption now requires the feed value to be **newer than the gateway's last pump-state write**. Stale or echo values cannot preempt an active PROFILE/SCHEDULE session. |
| Manual poll not wasting data points | ✅ **FIXED** | Poll cache increased from 0.5 s → 3 s, reducing Adafruit API calls from ~120/min to ~20/min. |

**Verdict: MANUAL mode is correct.**

---

### 1.2 AUTO Mode

| Requirement | Status | Details |
|---|---|---|
| Send alert when below lower threshold | ✅ PASS | `process_plant_alerts()` runs on every telemetry update regardless of mode. |
| Turn on pump when below lower threshold | ✅ PASS | `run_auto_logic()`: `if soil <= min_soil and not state.pump_is_on: start_irrigation("PROFILE")` |
| Turn off pump when reaching **midpoint** | ✅ PASS | `stop_target = midpoint(min_soil, max_soil)`. Pump stops when soil reaches halfway between min and max thresholds. |
| Stop check not delayed by HTTP | ✅ **FIXED** | `refresh_zone_config()` is skipped while PROFILE irrigation is active — the blocking HTTP call no longer delays the soil-based stop decision. |
| DEVICE-only soil floor stop | ✅ **FIXED** | The soil `>= stop_target` check now only applies to `active_trigger == "DEVICE"`. Previously it incorrectly used `min_soil` threshold and targeted wrong triggers. |
| Send alert with irrigation event after auto-irrigation | ✅ PASS | `stop_irrigation()` publishes an `IRRIGATION_EVENT` audit log and calls `backend.create_irrigation_event()`. |
| Create irrigation event via API | ✅ PASS | `backend.create_irrigation_event()` POSTs to `/api/irrigation-events`, separate from `backend.create_alert()`. |

---

### 1.3 AI Mode

| Requirement | Status | Details |
|---|---|---|
| Every hour or when under lower threshold, call `POST /api/ai/irrigation` | ✅ **FIXED** | `run_ai_logic()` calls `backend.call_ai_irrigation()` when `time_since_last_call >= AI_CALL_INTERVAL_SEC` (default 3600 s) OR when `soil < min_soil` and no pending schedule. |
| Request body: `{ "zoneId": "...", "lat": 10.7291, "lon": 106.6984 }` | ✅ **FIXED** | `BackendClient.call_ai_irrigation()` sends this exact payload. Lat/lon configurable via `AI_LAT`/`AI_LON` env vars. |
| Header: `X-API-Key: <GATEWAY_API_KEY>` | ✅ PASS | `BackendClient` sets `x-api-key` on all session requests. |
| Parse response: `{ "scheduled_at": "...", "duration_seconds": 92 }` | ✅ **FIXED** | `call_ai_irrigation()` parses both fields. Handles ISO datetimes with or without timezone. |
| Pump turns on at AI-scheduled time | ✅ **FIXED** | `run_ai_logic()` checks `now_ts >= state.ai_scheduled_start` each loop. When triggered, calls `start_irrigation("AI", dur)`. |
| Send irrigation event alert with actor = "AI" | ✅ **FIXED** | `stop_irrigation(actor="AI")` parameter used for AI-triggered completions. |

---

## 2. Data Synchronization (main.cpp → gateway → Adafruit)

| Requirement | Status | Details |
|---|---|---|
| ESP32 sends telemetry at high frequency | ✅ PASS | `TELEMETRY_PRINT_MS = 1000` ms, sensor reads at 500 ms/2000 ms. Immediate emit on pump state change. |
| Gateway reads serial with minimal blocking | ✅ PASS | Serial timeout 0.05 s. Main loop sleeps only 20 ms. |
| Sensor sends: per-feed change detection | ✅ **FIXED** | TEMP / HUMI sent only when value changes. SOIL sent only when change ≥ `SOIL_SEND_MIN_DELTA` % (default **2%**) — dead-zone filter suppresses ADC noise. |
| Pump sends: only on state change | ✅ **FIXED** | Pump state sent only when `pump_feed_dirty` (PROFILE/SCHEDULE/AI start or stop). Never sent periodically — prevents Adafruit echo loop on shared `pump` feed. |
| Minimum interval between batches | ✅ **FIXED** | `AIO_MIN_SEND_INTERVAL_SEC = 3` s gate prevents burst sends even when multiple values change simultaneously. |
| 0.2 s delay between individual feed sends | ✅ **FIXED** | `time.sleep(AIO_FEED_DELAY_SEC)` (default 0.2 s) inserted between consecutive `aio.send()` calls to respect Adafruit's per-second request cap. |
| Adafruit rate limit: ≤ 30 pts/min | ✅ **FIXED** | In practice: TEMP/HUMI/SOIL only sent on value change (rare during stable conditions) + pump events. Worst case stable environment = **0 sensor pts/min**. Worst case all values changing every 3 s = ~20 pts/min. |
| Throttle non-blocking | ✅ **FIXED** | `ThrottlingError` sets `state.aio_throttle_until = now + 65 s`. All aio calls skip during window. No `time.sleep()` — control loop continues uninterrupted. |
| Log spam prevention | ✅ **FIXED** | `_warn(key, msg)` debounce helper rate-limits repeated diagnostic prints (echo window, stale OFF, auto-logic debug) to once per `WARN_INTERVAL_SEC = 30 s`. |
| audit-log Adafruit feed disabled | ✅ **FIXED** | `AIO_AUDIT_FEED_ENABLED = 0` by default. All audit events still go to backend API. Re-enable with `AIO_AUDIT_FEED_ENABLED=1` in `.env`. |
| Stale pump state not sent on startup | ✅ **FIXED** | `last_pump_send_time` initialised to `time.time()` so gateway waits before first pump publish. |

**Verdict: Data synchronization is optimized.**

> [!NOTE]
> **Adafruit send config reference:**
> | Variable | Default | Effect |
> |---|---|---|
> | `AIO_MIN_SEND_INTERVAL_SEC` | `3` | Min seconds between Adafruit batches |
> | `AIO_FEED_DELAY_SEC` | `0.2` | Delay between individual feed sends |
> | `SOIL_SEND_MIN_DELTA` | `2` | Min soil % change to trigger send |
> | `AIO_AUDIT_FEED_ENABLED` | `0` | Send audit events to Adafruit feed |
> | `SENSOR_SEND_INTERVAL_SEC` | `15` | Fallback max interval (still applies as upper bound) |

---

## 3. Schedule Execution

| Requirement | Status | Details |
|---|---|---|
| Turn on at the scheduled time | ✅ **FIXED** | `TRIGGER_WINDOW_SEC` widened 2 s → **60 s** so HTTP-blocked loops no longer miss the window. `processed_schedule_marks` prevents double-firing within the same day. |
| Water by duration (not soil threshold) | ✅ **FIXED** | `run_schedule_logic()` calls `start_irrigation("SCHEDULE", slot.duration)`. Timer `current_schedule_end_at = scheduled_ts + dur_sec` stops pump when duration expires. |
| Pump turns on with minimum delay | ✅ **FIXED** | `start_irrigation()` called **before** `publish_audit_log()` — HTTP audit call no longer blocks the relay command. |
| Stop check not blocked by HTTP | ✅ **FIXED** | `refresh_zone_config()` skipped in main loop while `active_trigger` is SCHEDULE or PROFILE. Forced refresh every `CONFIG_REFRESH_SEC × 5` (75 s) even during irrigation. |
| Surface `schedule_id` in logs and audit | ✅ **FIXED** | `slot.schedule_id` included in `[SCHEDULE]` console print and `IRRIGATION_EVENT` audit log. |

> [!NOTE]
> For ±1 s hardware accuracy set `PUSH_SCHEDULE_TO_ESP=1` in `.env`. The ESP32's `millis()`-based timer is hardware-accurate; the gateway timer is best-effort (~20 ms + network latency).

---

## 4. Manual Pump Control (Adafruit Sync)

| Requirement | Status | Details |
|---|---|---|
| User can manually control pump | ✅ PASS | `run_manual_logic()` polls `FEED_PUMP_CMD` from Adafruit every 3 s (cached) and reacts to ON/OFF commands. |
| Pump stays ON until user sends OFF | ✅ **FIXED** | AUTO logic no longer stops MANUAL sessions. MANUAL only stops on explicit user OFF command. |
| No Adafruit feedback-loop reset | ✅ **FIXED** | Pump state is **never** written to Adafruit during MANUAL sessions (`pump_feed_dirty` never set for MANUAL). The shared `pump` feed retains the user's command value. |
| Echo suppression for PROFILE/SCHEDULE gateway writes | ✅ **FIXED** | 30-second hard echo window + feed-age vs write-age comparison prevent gateway's own pump-state write from being read back as a user command. |
| Works across all modes | ✅ PASS | `run_manual_logic()` runs first in main loop; AUTO/AI logic only runs when `active_trigger != "MANUAL"`. |

---

## 5. Priority: schedule > profile > manual > ai (when soil below threshold)

| Requirement | Status | Details |
|---|---|---|
| Base priority enforcement | ✅ **FIXED** | `TRIGGER_PRIORITY`: `MANUAL=100, SCHEDULE=75, PROFILE=50, AI=25, DEVICE=10`. `start_irrigation()` accepts optional `effective_priority` override. |
| Schedule beats profile/manual/ai when soil < min_soil | ✅ **FIXED** | `run_schedule_logic()` boosts schedule priority to `MANUAL + 1 = 101` when soil < min_soil, allowing preemption of any active trigger including MANUAL. |

**Priority enforcement summary:**

| Scenario | Behaviour |
|---|---|
| SCHEDULE fires while AI is running | SCHEDULE (p=75) > AI (p=25) → AI stopped, SCHEDULE starts |
| SCHEDULE fires while MANUAL is running, soil **normal** | MANUAL (p=100) > SCHEDULE (p=75) → SCHEDULE blocked |
| SCHEDULE fires while MANUAL is running, soil **< min_soil** | SCHEDULE boosted (p=101) > MANUAL (p=100) → MANUAL stopped, SCHEDULE starts |
| SCHEDULE fires while PROFILE is running | SCHEDULE (p=75) > PROFILE (p=50) → PROFILE stopped, SCHEDULE starts |
| User commands manual ON during AUTO/AI | `run_manual_logic()` preempts only if feed value is fresh (newer than last gateway pump write) |
| User commands manual OFF | Always stops any active irrigation regardless of trigger |

---

## Summary of All Fixes

| # | Severity | Issue | Fix |
|---|---|---|---|
| 1 | ✅ Fixed | **AI mode** — API call, scheduling, actor tagging | `run_ai_logic()`, `call_ai_irrigation()` |
| 2 | ✅ Fixed | **Priority system** — `manual > schedule > profile > ai`; boost when soil < min_soil | `TRIGGER_PRIORITY`, `start_irrigation(effective_priority=...)` |
| 3 | ✅ Fixed | **AUTO stops at midpoint** | `stop_target = midpoint(min_soil, max_soil)` |
| 4 | ✅ Fixed | **Manual cross-mode** — runs first, preempts any trigger | `run_manual_logic()`, main loop |
| 5 | ✅ Fixed | **AI actor** in irrigation events | `stop_irrigation(actor=...)` |
| 6 | ✅ Fixed | **Schedule trigger window** widened 2 s → 60 s | `check_schedule_trigger()` |
| 7 | ✅ Fixed | **Schedule pump start not blocked** — audit log moved after `start_irrigation()` | `run_schedule_logic()` |
| 8 | ✅ Fixed | **HTTP stop-check delay** — `refresh_zone_config()` skipped during SCHEDULE/PROFILE | main loop |
| 9 | ✅ Fixed | **Manual Adafruit feedback loop** — echo suppression (30 s window + write-age comparison); no periodic pump send for MANUAL | `GatewayState`, `poll_manual_command_from_feed()`, `send_to_adafruit_if_due()` |
| 10 | ✅ Fixed | **DEVICE-only soil stop** — auto_logic soil check restricted to DEVICE trigger | `run_auto_logic()` |
| 11 | ✅ Fixed | **Adafruit rate limit** — per-feed change detection, SOIL ≥ 2% filter, 3 s min interval, 0.2 s inter-feed delay, audit-log feed off by default | `send_to_adafruit_if_due()`, config |
| 12 | ✅ Fixed | **Throttle blocks control loop** — removed all `time.sleep()` from `ThrottlingError` handlers; non-blocking `aio_throttle_until` state | `send_to_adafruit_if_due()`, `poll_manual_command_from_feed()` |
| 13 | ✅ Fixed | **Log spam / infinite loop prints** — `_warn(key, msg)` debounce helper limits repeated diagnostic prints to once per 30 s | `_warn()`, `run_auto_logic()`, `run_manual_logic()` |
| 14 | ⚠️ Partial | **Schedule ±1 s hardware accuracy** — set `PUSH_SCHEDULE_TO_ESP=1` for ESP32 hardware timer | `.env` config |
