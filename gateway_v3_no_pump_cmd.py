import os
import time
import json
import re
import serial
import requests
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, UTC
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from Adafruit_IO import Client
from Adafruit_IO.errors import ThrottlingError

# ==========================================================
# CONFIG
# ==========================================================
AIO_USERNAME = os.getenv("AIO_USERNAME", "")
AIO_KEY = os.getenv("AIO_KEY", "")

FEED_TEMP = os.getenv("FEED_TEMP", "temperature")
FEED_HUM = os.getenv("FEED_HUM", "humidity")
FEED_SOIL = os.getenv("FEED_SOIL", "soil")
FEED_PUMP = os.getenv("FEED_PUMP", "pump")
FEED_PUMP_CMD = os.getenv("FEED_PUMP_CMD", FEED_PUMP)
FEED_PUMP_STATE = os.getenv("FEED_PUMP_STATE", FEED_PUMP)
MANUAL_FEED_ECHO_SUPPRESS_SEC = float(os.getenv("MANUAL_FEED_ECHO_SUPPRESS_SEC", "2.0"))
FEED_AUDIT = os.getenv("FEED_AUDIT", "audit-log")

SERIAL_PORT = os.getenv("SERIAL_PORT", "COM4")
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "115200"))

API_BASE_URL = os.getenv("API_BASE_URL", "")
ZONE_ID = os.getenv("ZONE_ID", "")
API_TOKEN = os.getenv("API_TOKEN", "")
SCHEDULE_ID = os.getenv("SCHEDULE_ID", "")

CONFIG_REFRESH_SEC = int(os.getenv("CONFIG_REFRESH_SEC", "15"))
SEND_INTERVAL_SEC = int(os.getenv("SEND_INTERVAL_SEC", "10"))
ALERT_INTERVAL_SEC = int(os.getenv("ALERT_INTERVAL_SEC", "300"))
DEVICE_OFFLINE_SEC = int(os.getenv("DEVICE_OFFLINE_SEC", "30"))
PROFILE_MIN_RUN_SEC = int(os.getenv("PROFILE_MIN_RUN_SEC", "0"))
PUMP_OFF_GRACE_SEC = int(os.getenv("PUMP_OFF_GRACE_SEC", "3"))
SEND_IMMEDIATE_ON_CHANGE = str(os.getenv("SEND_IMMEDIATE_ON_CHANGE", "1")).strip().lower() in ("1", "true", "yes", "on")
# When disabled, schedules are enforced only by the gateway (recommended).
PUSH_SCHEDULE_TO_ESP = str(os.getenv("PUSH_SCHEDULE_TO_ESP", "0")).strip().lower() in ("1", "true", "yes", "on")
# Optional: compute SOIL percent on the gateway from raw ADC value reported by device.
# Set SOIL_RAW_DRY/SOIL_RAW_WET to match device calibration if needed.
SOIL_RAW_DRY = int(os.getenv("SOIL_RAW_DRY", "4095"))
SOIL_RAW_WET = int(os.getenv("SOIL_RAW_WET", "1200"))
COMPUTE_SOIL_FROM_RAW = str(os.getenv("COMPUTE_SOIL_FROM_RAW", "1")).strip().lower() in ("1", "true", "yes", "on")
STOP_HYSTERESIS_COUNT = int(os.getenv("STOP_HYSTERESIS_COUNT", "1"))

# AI mode config
AI_CALL_INTERVAL_SEC = int(os.getenv("AI_CALL_INTERVAL_SEC", "3600"))  # seconds between proactive AI calls
AI_LAT = float(os.getenv("AI_LAT", "10.7291"))
AI_LON = float(os.getenv("AI_LON", "106.6984"))

# How old (seconds) a manual Adafruit feed value may be and still be treated as a live
# command against a gateway-controlled trigger (SCHEDULE / PROFILE / AI).
# A stale OFF value (e.g. user pressed OFF yesterday) must not kill today's schedule.
# Set to 0 to always apply every feed value regardless of age.
MANUAL_FEED_STALE_SEC = int(os.getenv("MANUAL_FEED_STALE_SEC", "120"))

GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_RECEIVER = os.getenv("GMAIL_RECEIVER", "")

# ----------------------------------------------------------
# Local forced schedule (can be enabled via env var for quick testing)
# Set FORCE_LOCAL_SCHEDULE to true/1 to inject a local timeslot when backend schedule is missing.
# ----------------------------------------------------------
# read boolean-like env var values
FORCE_LOCAL_SCHEDULE = str(os.getenv("FORCE_LOCAL_SCHEDULE", "")).strip().lower() in ("1", "true", "yes", "on")
FORCE_SCHEDULE_START = os.getenv("FORCE_SCHEDULE_START", "")  # HH:MM local
FORCE_SCHEDULE_DURATION_MIN = int(os.getenv("FORCE_SCHEDULE_DURATION_MIN", ""))
FORCE_SCHEDULE_DAYS = os.getenv("FORCE_SCHEDULE_DAYS", "").split(",")

# ==========================================================
# HELPERS
# ==========================================================
DAY_NAME_TO_INDEX = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

def now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")

def hhmm_now() -> str:
    return datetime.now().strftime("%H:%M")

def weekday_name_now() -> str:
    return datetime.now().strftime("%A")

def midpoint(min_value: int, max_value: int) -> int:
    return int((min_value + max_value) / 2)

def normalize_mode(mode: Optional[str]) -> str:
    if not mode:
        return "MANUAL"
    return str(mode).strip().upper()

def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default

def coerce_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return bool(int(value))
    s = str(value).strip().lower()
    if s in ("1", "true", "on", "yes", "open", "start", "opened"):
        return True
    if s in ("0", "false", "off", "no", "close", "stop", "closed"):
        return False
    return None


def pick_manual_pump_state(*sources: Any) -> Optional[bool]:
    candidate_keys = (
        "manualPumpOn", "manualPumpState", "manualPump",
        "pumpOn", "pumpState", "relayOn", "relayState",
        "isPumpOn", "isRelayOn", "manualRelayOn",
        "pump", "relay", "value", "state",
    )
    for src in sources:
        if isinstance(src, dict):
            for key in candidate_keys:
                if key in src:
                    parsed = coerce_bool(src.get(key))
                    if parsed is not None:
                        return parsed
            nested = src.get("manual")
            if isinstance(nested, dict):
                parsed = pick_manual_pump_state(nested)
                if parsed is not None:
                    return parsed
    return None

def normalize_days(raw_days: Any) -> List[str]:
    if raw_days is None:
        return []
    if isinstance(raw_days, list):
        output: List[str] = []
        for item in raw_days:
            day = str(item).strip()
            if day in DAY_NAME_TO_INDEX:
                output.append(day)
        return output
    return []


def parse_start_time(raw_time: Any) -> str:
    """Parse a schedule slot start time and preserve seconds when present.

    Accepts:
    - `HH:MM`
    - `HH:MM:SS`
    - ISO datetime strings

    Returns local time as `HH:MM:SS`.
    """
    if not raw_time:
        return "06:00:00"
    s = str(raw_time).strip()
    try:
        if "T" in s:
            s2 = s.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s2)
            local_dt = dt.astimezone()
            return local_dt.strftime("%H:%M:%S")
    except Exception:
        pass

    m = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", s)
    if m:
        hh = m.group(1).zfill(2)
        mm = m.group(2)
        ss = m.group(3) or "00"
        return f"{hh}:{mm}:{ss}"

    return "06:00:00"


def parse_hms(value: str) -> tuple[int, int, int]:
    parts = str(value).split(":")
    hh = int(parts[0]) if len(parts) >= 1 else 0
    mm = int(parts[1]) if len(parts) >= 2 else 0
    ss = int(parts[2]) if len(parts) >= 3 else 0
    return hh, mm, ss

# device keys and friendly names
DEVICE_KEYS = ["TEMP", "HUMI", "SOIL", "PUMP"]
DEVICE_FRIENDLY: Dict[str, str] = {
    "TEMP": "Temperature sensor",
    "HUMI": "Humidity sensor",
    "SOIL": "Soil sensor",
    "PUMP": "Relay",
}

# Trigger priority: higher number wins. Manual always beats everything.
TRIGGER_PRIORITY: Dict[str, int] = {
    "MANUAL": 100,
    "SCHEDULE": 75,
    "PROFILE": 50,
    "AI": 25,
    "DEVICE": 10,
}

# ==========================================================
# DATA MODELS
# ==========================================================
@dataclass
class TimeSlot:
    slot_id: str
    start_time: str
    duration: int
    days: List[str] = field(default_factory=list)
    schedule_id: str = ""

@dataclass
class ZoneProfile:
    profile_id: str = ""
    name: str = ""
    min_soil: int = 30
    max_soil: int = 70
    mode: str = "MANUAL"

@dataclass
class ZoneConfig:
    zone_id: str = ""
    zone_name: str = ""
    profile_id: Optional[str] = None
    schedule_id: Optional[str] = None
    profile: ZoneProfile = field(default_factory=ZoneProfile)
    schedule_name: str = ""
    time_slots: List[TimeSlot] = field(default_factory=list)
    manual_pump_on: Optional[bool] = None

# ==========================================================
# BACKEND CLIENT
# ==========================================================
class BackendClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        if token:
            self.session.headers.update({"x-api-key": token})

    def _get(self, path: str) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}{path}", timeout=10, allow_redirects=False)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = self.session.post(
            f"{self.base_url}{path}",
            data=json.dumps(payload),
            timeout=10,
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.text:
            try:
                return response.json()
            except Exception:
                return None
        return None

    @staticmethod
    def _unwrap(data: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(data, dict) and isinstance(data.get("data"), dict):
            return data["data"]
        return data

    def fetch_zone_config(self, zone_id: str) -> ZoneConfig:
        zone = self._unwrap(self._get(f"/api/zones/{zone_id}"))
        profile = {}
        schedule = {}

        profile_id = zone.get("profileId")
        schedule_id = zone.get("scheduleId")

        # Allow overriding schedule via environment (optional)
        # If SCHEDULE_ID is set, use it instead of the schedule referenced by the zone.
        try:
            if SCHEDULE_ID:
                schedule_id = SCHEDULE_ID
                print(f"Overriding schedule with SCHEDULE_ID from env: {SCHEDULE_ID}")
        except Exception:
            pass

        if profile_id:
            profile = self._unwrap(self._get(f"/api/profiles/{profile_id}"))
        if schedule_id:
            schedule = self._unwrap(self._get(f"/api/schedules/{schedule_id}"))

        raw_slots = schedule.get("timeSlots") or []
        time_slots: List[TimeSlot] = []
        for slot in raw_slots:
            time_slots.append(
                TimeSlot(
                    slot_id=str(slot.get("id", "")),
                    start_time=parse_start_time(slot.get("startTime", "06:00")),
                    duration=safe_int(slot.get("duration"), 0),
                    days=normalize_days(slot.get("days")),
                    schedule_id=str(slot.get("scheduleId", schedule_id or "")),
                )
            )

        manual_pump_on = pick_manual_pump_state(zone, profile)

        return ZoneConfig(
            zone_id=str(zone.get("id", zone_id)),
            zone_name=str(zone.get("name", "")),
            profile_id=profile_id,
            schedule_id=schedule_id,
            profile=ZoneProfile(
                profile_id=str(profile.get("id", profile_id or "")),
                name=str(profile.get("name", "")),
                min_soil=safe_int(profile.get("minMoisture"), 30),
                max_soil=safe_int(profile.get("maxMoisture"), 70),
                mode=normalize_mode(profile.get("mode")),
            ),
            schedule_name=str(schedule.get("name", "")),
            time_slots=time_slots,
            manual_pump_on=manual_pump_on,
        )

    def create_alert(self, *, zone_id: Optional[str], message: str, severity: str, alert_type: str, actor: str) -> None:
        payload = {
            "type": alert_type,
            "actor": actor,
            "message": message,
            "severity": severity,
            "zoneId": zone_id,
        }
        self._post("/api/alerts", payload)

    def create_irrigation_event(self, *, zone_id: str, start_time: str, end_time: Optional[str] = None, duration: Optional[int] = None) -> None:
        payload: Dict[str, Any] = {"zoneId": zone_id, "startTime": start_time}
        if end_time is not None:
            payload["endTime"] = end_time
        if duration is not None:
            payload["duration"] = duration
        self._post("/api/irrigation-events", payload)

    def call_ai_irrigation(self, zone_id: str, lat: float = 10.7291, lon: float = 106.6984) -> Optional[tuple]:
        """POST /api/ai/irrigation and return (scheduled_at_epoch, duration_seconds) or None."""
        payload: Dict[str, Any] = {"zoneId": zone_id, "lat": lat, "lon": lon}
        result = self._post("/api/ai/irrigation", payload)
        if not isinstance(result, dict):
            return None
        scheduled_at_str = result.get("scheduled_at")
        duration_seconds = result.get("duration_seconds")
        if scheduled_at_str is None or duration_seconds is None:
            return None
        try:
            s = str(scheduled_at_str).strip()
            # Try with timezone first (Z or +HH:MM)
            try:
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            except ValueError:
                # No timezone — treat as local naive datetime
                dt = datetime.fromisoformat(s)
            epoch = dt.timestamp()
            return epoch, int(duration_seconds)
        except Exception as exc:
            print("AI irrigation response parse error:", exc)
            return None

    def update_devices_last_active(self, zone_id: str, devices: Dict[str, str]) -> None:
        """Update last active timestamps for devices in the backend.

        payload example: { "zoneId": "zone1", "devices": {"TEMP": "2026-04-16T...Z", ...} }
        """
        # If base_url is not configured, skip
        if not self.base_url:
            return

        payload = {"zoneId": zone_id, "devices": devices}
        url = f"{self.base_url}/api/devices/last-active"
        # try POST/PUT/PATCH; if server disallows all, fall back to GET with query params
        try:
            methods = ["post", "put", "patch"]
            did_call = False
            for m in methods:
                func = getattr(self.session, m)
                resp = func(url, data=json.dumps(payload), timeout=10)
                did_call = True
                # if server returns 405, try next method
                if resp.status_code == 405:
                    continue
                # successful (or other error) -> raise if error, otherwise we're done
                resp.raise_for_status()
                print(f"Update devices last active via {m.upper()} OK")
                return

            # if we reach here and we've tried HTTP methods but all were 405, try GET fallback
            if did_call:
                params = {"zoneId": zone_id}
                params.update(devices)
                resp = self.session.get(url, params=params, timeout=10)
                resp.raise_for_status()
                print("Update devices last active via GET OK")
                return
        except Exception as exc:
            # If API doesn't expose this endpoint, quietly ignore 404 to avoid noisy logs
            try:
                resp = getattr(exc, 'response', None)
                if resp is not None and getattr(resp, 'status_code', None) == 404:
                    # endpoint not found on this backend; skip without error
                    return
            except Exception:
                pass
            print("Update devices last active error:", exc)

# ==========================================================
# EMAIL
# ==========================================================
def send_email(subject: str, body: str):
    if not (GMAIL_SENDER and GMAIL_APP_PASSWORD and GMAIL_RECEIVER):
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_SENDER
        msg["To"] = GMAIL_RECEIVER
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, GMAIL_RECEIVER, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as exc:
        print("Email error:", exc)

# ==========================================================
# GATEWAY STATE
# ==========================================================
class GatewayState:
    def __init__(self, zone_id: str):
        self.zone_id = zone_id
        self.zone_cfg = ZoneConfig(zone_id=zone_id)
        self.latest_data: Optional[Dict[str, Any]] = None
        self.last_send_time = 0.0
        self.last_alert_time = 0.0
        self.last_config_refresh = 0.0
        # per-device last seen timestamps (epoch seconds)
        self.device_last_seen: Dict[str, float] = {k: 0.0 for k in DEVICE_KEYS}
        self.pump_is_on = False
        self.active_trigger: Optional[str] = None
        self.current_watering_started_at: Optional[float] = None
        self.current_schedule_end_at: Optional[float] = None
        self.current_schedule_slot_id: Optional[str] = None
        self.processed_schedule_marks: Dict[str, bool] = {}
        # when True, ignore audit log events coming from device for irrigation START/STOP
        self.suppress_device_audit: bool = False
        # last published irrigation event signature to avoid duplicates
        self.last_irrigation_event_signature: Optional[str] = None
        # last time we published an irrigation completed event (epoch seconds)
        self.last_irrigation_published_at: float = 0.0
        # minimum profile-driven run end timestamp (epoch seconds)
        self.profile_min_end_at: Optional[float] = None
        # consecutive readings above stop target (hysteresis counter)
        self.stop_above_count: int = 0
        # ignore short pump telemetry OFF transitions that occur immediately after we commanded ON
        self.ignore_pump_off_until: float = 0.0
        # per-device offline logged flags
        self.device_offline_logged: Dict[str, bool] = {k: False for k in DEVICE_KEYS}
            # last telemetry values sent to Adafruit/backend
        self.last_sent_data: Dict[str, Any] = {}
        self.last_manual_command: Optional[int] = None
        self.last_manual_poll_time: float = 0.0
        self.last_manual_feed_value: Optional[int] = None
        self.last_manual_command_at: float = 0.0
        self.pending_manual_state: Optional[int] = None
        # Age (seconds) of the last successfully read Adafruit feed value.
        # Initialized to infinity so startup never treats an old feed value as fresh.
        self.last_manual_feed_age_sec: float = float("inf")
        # AI mode state
        self.last_ai_call_time: float = 0.0          # epoch of last successful AI API call
        self.ai_scheduled_start: Optional[float] = None   # epoch when AI wants pump to start
        self.ai_duration_sec: Optional[int] = None   # AI-prescribed run duration
        # Set True only when AUTO/SCHEDULE/AI changes pump state; consumed once by
        # send_to_adafruit_if_due then cleared. MANUAL never sets this flag.
        self.pump_feed_dirty: bool = False

    def mark_device_seen(self, device: str):
        """Record that a given device (e.g. 'TEMP') was seen now.

        If that device was previously logged offline, emit an INFO audit.
        """
        now_ts = time.time()
        self.device_last_seen[device] = now_ts
        if self.device_offline_logged.get(device):
            publish_audit_log(
                zone_id=self.zone_cfg.zone_id,
                zone_name=self.zone_cfg.zone_name,
                severity="INFO",
                alert_type="DEVICE_STATUS",
                actor="SYSTEM",
                message=f"{DEVICE_FRIENDLY.get(device, device)} is back online",
            )
            self.device_offline_logged[device] = False

# ==========================================================
# CLIENTS
# ==========================================================
aio = Client(AIO_USERNAME, AIO_KEY)
backend = BackendClient(API_BASE_URL, API_TOKEN)
state = GatewayState(ZONE_ID)
# reduce serial timeout so gateway loop is more responsive
ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.05)

print("Gateway started...")

# ==========================================================
# AUDIT LOG PUBLISHER
# ==========================================================
def publish_audit_log(*, zone_id: Optional[str], zone_name: str, severity: str, alert_type: str, actor: str, message: str):
    try:
        backend.create_alert(
            zone_id=zone_id,
            message=message,
            severity=severity,
            alert_type=alert_type,
            actor=actor,
        )
    except Exception as exc:
        print("Create alert error:", exc)

    try:
        payload = {
            "zoneId": zone_id,
            "zoneName": zone_name or zone_id,
            "severity": severity,
            "type": alert_type,
            "actor": actor,
            "message": message,
            "ts": now_iso(),
        }
        aio.send(FEED_AUDIT, json.dumps(payload, ensure_ascii=False))
    except Exception as exc:
        print("Send audit feed error:", exc)

# ==========================================================
# DEVICE COMMANDS
# ==========================================================
def send_pump_command(value: int):
    cmd = f"!CMD=PUMP;VALUE={value}#\n"
    ser.write(cmd.encode("utf-8"))
    state.pump_is_on = value == 1
    print("Sent to ESP32:", cmd.strip())


def send_time_to_esp():
    try:
        cmd = f"!TIME={int(time.time())}#\n"
        ser.write(cmd.encode("utf-8"))
        print("Sent time to ESP32:", cmd.strip())
    except Exception as exc:
        print("Send time to ESP32 error:", exc)


def send_zone_to_esp():
    try:
        zid = state.zone_cfg.zone_id or ZONE_ID
        if not zid:
            return
        cmd = f"!ZONE={zid}#\n"
        ser.write(cmd.encode("utf-8"))
        print("Sent zone to ESP32:", cmd.strip())
    except Exception as exc:
        print("Send zone to ESP32 error:", exc)


def send_schedule_to_esp():
    try:
        if not state.zone_cfg or not state.zone_cfg.time_slots:
            return
        for slot in state.zone_cfg.time_slots:
            # compute next occurrence epoch (local time interpretation)
            try:
                hh, mm = 0, 0
                try:
                    parts = slot.start_time.split(":")
                    hh = int(parts[0])
                    mm = int(parts[1])
                except Exception:
                    pass

                # determine applicable weekdays (0=Monday..6=Sunday)
                wanted_days = [DAY_NAME_TO_INDEX[d] for d in slot.days if d in DAY_NAME_TO_INDEX]

                from datetime import datetime as _dt, timedelta as _td

                now_local = _dt.now()
                found_dt = None
                for offset in range(0, 8):
                    cand = now_local + _td(days=offset)
                    if wanted_days and cand.weekday() not in wanted_days:
                        continue
                    cand_dt = _dt(cand.year, cand.month, cand.day, hh, mm, 0)
                    if cand_dt >= now_local:
                        found_dt = cand_dt
                        break
                if not found_dt:
                    # fallback to today +1
                    found_dt = now_local + _td(days=1)
                    found_dt = _dt(found_dt.year, found_dt.month, found_dt.day, hh, mm, 0)

                # convert local struct_time to epoch seconds (local)
                epoch_local = int(time.mktime(found_dt.timetuple()))
                # backend schedules express duration in seconds (e.g. '10s' in UI)
                # so send the duration through as-is (seconds)
                duration_sec = int(slot.duration)

                zid = state.zone_cfg.zone_id or ZONE_ID
                cmd = f"!SCHEDABS;ZONE={zid};ID={slot.slot_id};START_TS={epoch_local};DUR={duration_sec}#\n"
                ser.write(cmd.encode("utf-8"))
                print("Sent schedule to ESP32:", cmd.strip())
                time.sleep(0.02)
            except Exception as exc:
                print("Send schedule slot error:", exc)
    except Exception as exc:
        print("Send schedule to ESP32 error:", exc)

# ==========================================================
# IRRIGATION ACTIONS
# ==========================================================
def start_irrigation(trigger: str, duration_sec: Optional[int] = None, started_ts: Optional[float] = None):
    # Priority check: higher-priority trigger can preempt a running lower-priority one.
    if state.pump_is_on:
        current_priority = TRIGGER_PRIORITY.get(state.active_trigger or "", 0)
        new_priority = TRIGGER_PRIORITY.get(trigger, 0)
        if new_priority > current_priority:
            print(
                f"[PRIORITY] {trigger} (p={new_priority}) preempting "
                f"{state.active_trigger} (p={current_priority})"
            )
            stop_irrigation(
                f"preempted by higher-priority trigger: {trigger}",
                force=True,
            )
            # fall through to start the new irrigation below
        else:
            print(
                f"[PRIORITY] {trigger} (p={new_priority}) blocked by "
                f"{state.active_trigger} (p={current_priority})"
            )
            return
    state.active_trigger = trigger
    now_ts = time.time()
    effective_start_ts = float(started_ts) if started_ts is not None else now_ts
    state.current_watering_started_at = effective_start_ts
    state.current_schedule_end_at = (effective_start_ts + duration_sec) if trigger in ("SCHEDULE", "PROFILE", "AI") and duration_sec is not None else None

    # For PROFILE-triggered runs, enforce a minimum run duration to avoid rapid on/off toggling
    if trigger == "PROFILE":
        state.profile_min_end_at = now_ts + PROFILE_MIN_RUN_SEC
    else:
        state.profile_min_end_at = None

    # reset hysteresis counter when a new irrigation starts
    state.stop_above_count = 0

    # If this irrigation was started by schedule or profile, suppress device-originated
    # audit log entries for START/STOP to avoid duplicate events. Set suppression
    # before sending the ON command to avoid races with immediate telemetry.
    state.suppress_device_audit = True if trigger in ("SCHEDULE", "PROFILE", "AI") else False
    # ignore pump OFF telemetry for a short grace window after we command ON
    state.ignore_pump_off_until = now_ts + PUMP_OFF_GRACE_SEC

    # If this irrigation is gateway-initiated (AUTO/SCHEDULE/AI), mark pump feed
    # as needing a publish so Adafruit dashboard reflects the new state exactly once.
    if trigger in ("PROFILE", "SCHEDULE", "AI"):
        state.pump_feed_dirty = True

    # finally, command the pump ON
    send_pump_command(1)
    # We intentionally do NOT publish a "start" irrigation event here.
    # The system should only create a single irrigation event when the irrigation completes.
    try:
        print(f"[IRRIGATION] started by {trigger} for zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id} (min_end_at={state.profile_min_end_at})")
    except Exception:
        pass

def stop_irrigation(reason: str, started_ts: Optional[float] = None, force: bool = False, actor: str = "SYSTEM"):
    """Stop irrigation and publish a single completed irrigation event.

    If `started_ts` is provided use it as the start time; otherwise use the
    recorded `state.current_watering_started_at`. The function is idempotent
    and will avoid publishing duplicate identical events.
    """
    # Determine if there is meaningful irrigation to stop
    recorded_start = state.current_watering_started_at
    if not recorded_start and not started_ts and not force:
        # nothing to stop/record
        return

    started_ts_val = float(started_ts) if started_ts else (float(recorded_start) if recorded_start else time.time())
    ended_ts = time.time()
    duration_sec = max(0, int(ended_ts - started_ts_val))

    # Build signature (seconds precision) to avoid duplicate publishes
    start_iso = datetime.fromtimestamp(started_ts_val, UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    end_iso = datetime.fromtimestamp(ended_ts, UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    signature = f"{start_iso}|{end_iso}|{duration_sec}"
    if state.last_irrigation_event_signature == signature:
        # already published this exact event
        # still ensure internal state is cleared
        state.suppress_device_audit = False
        state.active_trigger = None
        state.current_watering_started_at = None
        state.current_schedule_end_at = None
        state.current_schedule_slot_id = None
        state.pump_is_on = False
        state.profile_min_end_at = None
        state.ignore_pump_off_until = 0.0
        state.stop_above_count = 0
        return

    # Turn pump off if it appears to be on
    # Always attempt to send OFF command to device to ensure relay is turned off
    try:
        send_pump_command(0)
        print(f"[IRRIGATION] stop requested: {reason}")
    except Exception:
        pass

    # attempt to persist irrigation event to backend
    try:
        backend.create_irrigation_event(
            zone_id=state.zone_cfg.zone_id,
            start_time=start_iso,
            end_time=end_iso,
            duration=duration_sec,
        )
    except Exception as exc:
        print("Create irrigation event error:", exc)

    # publish a single structured irrigation completed event
    event_payload = {"startTime": start_iso, "endTime": end_iso, "duration": duration_sec}
    publish_audit_log(
        zone_id=state.zone_cfg.zone_id,
        zone_name=state.zone_cfg.zone_name,
        severity="INFO",
        alert_type="IRRIGATION_EVENT",
        actor=actor,
        message=f"Irrigation completed for zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id}: {json.dumps(event_payload, ensure_ascii=False)}",
    )

    # mark signature and clear suppression/state
    state.last_irrigation_event_signature = signature
    # Flag pump feed for publish if this was a gateway-owned irrigation session.
    if state.active_trigger in ("PROFILE", "SCHEDULE", "AI"):
        state.pump_feed_dirty = True
    state.suppress_device_audit = False
    state.active_trigger = None
    state.current_watering_started_at = None
    state.current_schedule_end_at = None
    state.current_schedule_slot_id = None
    state.profile_min_end_at = None
    state.ignore_pump_off_until = 0.0
    state.stop_above_count = 0

# ==========================================================
# CONFIG REFRESH
# ==========================================================
def sync_runtime_to_esp(include_schedule: bool = False):
    """Send current runtime context to ESP32.

    By default we do NOT push schedules to ESP32, because gateway-side schedule logic
    already exists and duplicate schedule ownership causes conflicts with AUTO logic.
    Set PUSH_SCHEDULE_TO_ESP=1 if you explicitly want the ESP to own schedule timing.
    """
    try:
        send_time_to_esp()
    except Exception:
        pass
    try:
        send_zone_to_esp()
    except Exception:
        pass
    if include_schedule and PUSH_SCHEDULE_TO_ESP:
        try:
            send_schedule_to_esp()
        except Exception:
            pass


def refresh_zone_config(force: bool = False):
    if not force and time.time() - state.last_config_refresh < CONFIG_REFRESH_SEC:
        return

    try:
        old_cfg = state.zone_cfg
        new_cfg = backend.fetch_zone_config(state.zone_id)
        state.zone_cfg = new_cfg
        state.last_config_refresh = time.time()

        # If requested, ensure a local forced schedule exists (user-requested)
        try:
            if FORCE_LOCAL_SCHEDULE:
                # create normalized days list and avoid duplicates
                forced_days = [d.strip() for d in FORCE_SCHEDULE_DAYS if d.strip()]
                forced_start = parse_start_time(FORCE_SCHEDULE_START)
                forced_duration = int(FORCE_SCHEDULE_DURATION_MIN)
                found = False
                for s in state.zone_cfg.time_slots:
                    if s.start_time == forced_start and s.duration == forced_duration:
                        # ensure days cover the forced days
                        if set(forced_days).issubset(set(s.days)):
                            found = True
                            break
                if not found:
                    slot_id = f"local-{forced_start.replace(":","")}-{forced_duration}m"
                    new_slot = TimeSlot(slot_id=slot_id, start_time=forced_start, duration=forced_duration, days=forced_days, schedule_id="local")
                    state.zone_cfg.time_slots.append(new_slot)
                    print(f"Injected local schedule -> start={forced_start}, duration={forced_duration}m, days={forced_days}")
                    # Keep ESP32 in sync, but let gateway own schedule timing by default.
                    sync_runtime_to_esp(include_schedule=True)
        except Exception as exc:
            print("Ensure local schedule error:", exc)

        print(
            f"Zone config refreshed -> zone={new_cfg.zone_name}, mode={new_cfg.profile.mode}, "
            f"min={new_cfg.profile.min_soil}, max={new_cfg.profile.max_soil}, slots={len(new_cfg.time_slots)}, manual_pump_on={new_cfg.manual_pump_on}"
        )

        # Always keep time/zone synced to ESP32. Schedule push is optional.
        sync_runtime_to_esp(include_schedule=False)

        # if old_cfg.profile.mode != new_cfg.profile.mode:
        #     publish_audit_log(
        #         zone_id=new_cfg.zone_id,
        #         zone_name=new_cfg.zone_name,
        #         severity="INFO",
        #         alert_type="DEVICE_STATUS",
        #         actor="SYSTEM",
        #         message=f"Profile mode changed from {old_cfg.profile.mode} to {new_cfg.profile.mode}",
        #     )

        if old_cfg.profile.min_soil != new_cfg.profile.min_soil or old_cfg.profile.max_soil != new_cfg.profile.max_soil:
            # publish_audit_log(
            #     zone_id=new_cfg.zone_id,
            #     zone_name=new_cfg.zone_name,
            #     severity="INFO",
            #     alert_type="PLANT_STATUS",
            #     actor="SYSTEM",
            #     message=f"Profile thresholds updated: min={new_cfg.profile.min_soil}%, max={new_cfg.profile.max_soil}%",
            # )
            if state.pump_is_on and state.latest_data is not None:
                soil = safe_int(state.latest_data.get("SOIL"), 0)
                stop_target = new_cfg.profile.max_soil
                if state.active_trigger in ("PROFILE", None) and soil >= stop_target:
                    stop_irrigation(f"profile changed and soil already >= profile max threshold {stop_target}%")

        old_schedule_sig = [(slot.slot_id, slot.start_time, tuple(slot.days), slot.duration) for slot in old_cfg.time_slots]
        new_schedule_sig = [(slot.slot_id, slot.start_time, tuple(slot.days), slot.duration) for slot in new_cfg.time_slots]
        if old_schedule_sig != new_schedule_sig:
            publish_audit_log(
                zone_id=new_cfg.zone_id,
                zone_name=new_cfg.zone_name,
                severity="INFO",
                alert_type="IRRIGATION_EVENT",
                actor="SYSTEM",
                message=f"Schedule updated for zone {new_cfg.zone_name or new_cfg.zone_id}",
            )
            # Keep ESP32 runtime in sync. Gateway remains the default schedule owner.
            sync_runtime_to_esp(include_schedule=True)

    except Exception as exc:
        print("Fetch zone config error:", exc)
        publish_audit_log(
            zone_id=state.zone_cfg.zone_id,
            zone_name=state.zone_cfg.zone_name,
            severity="WARNING",
            alert_type="DEVICE_STATUS",
            actor="SYSTEM",
            message=f"Failed to refresh zone/profile/schedule config: {exc}",
        )

# ==========================================================
# MODE LOGIC
# ==========================================================
def check_schedule_trigger() -> Optional[tuple[TimeSlot, float]]:
    # Use exact local seconds and a tight trigger window so schedule timing is precise.
    now_dt = datetime.now().astimezone()
    current_day = now_dt.strftime("%A")
    today = now_dt.strftime("%Y-%m-%d")
    now_ts = time.time()
    TRIGGER_WINDOW_SEC = 2.0

    for slot in state.zone_cfg.time_slots:
        if slot.days and current_day not in slot.days:
            continue

        try:
            hh, mm, ss = parse_hms(slot.start_time)
        except Exception:
            continue

        try:
            scheduled_dt = now_dt.replace(hour=hh, minute=mm, second=ss, microsecond=0)
            scheduled_ts = scheduled_dt.timestamp()
        except Exception:
            continue

        slot_key = slot.slot_id or f"{slot.start_time}-{slot.duration}-{','.join(slot.days)}"
        mark = f"{today}:{slot_key}"
        if state.processed_schedule_marks.get(mark):
            continue

        if now_ts >= scheduled_ts and now_ts < scheduled_ts + TRIGGER_WINDOW_SEC:
            state.processed_schedule_marks[mark] = True
            return slot, scheduled_ts

    return None

def poll_manual_command_from_feed() -> Optional[bool]:
    now_ts = time.time()
    if now_ts - state.last_manual_poll_time < 0.5:
        if state.last_manual_feed_value is None:
            return None
        return bool(state.last_manual_feed_value)

    state.last_manual_poll_time = now_ts
    try:
        pkt = aio.receive(FEED_PUMP_CMD)
        raw = getattr(pkt, "value", None)
        parsed = coerce_bool(raw)
        if parsed is None:
            return None
        # Compute age of this feed value from its created_at timestamp so we can
        # distinguish a live command from a stale historical value.
        try:
            created_at_str = getattr(pkt, "created_at", None)
            if created_at_str:
                created_dt = datetime.fromisoformat(str(created_at_str).replace("Z", "+00:00"))
                state.last_manual_feed_age_sec = now_ts - created_dt.timestamp()
            else:
                state.last_manual_feed_age_sec = 0.0  # no timestamp → treat as fresh
        except Exception:
            state.last_manual_feed_age_sec = 0.0
        state.last_manual_feed_value = 1 if parsed else 0
        return parsed
    except Exception:
        if state.last_manual_feed_value is None:
            return None
        return bool(state.last_manual_feed_value)


def run_manual_logic():
    """Run manual pump control. Always called regardless of profile mode.

    Manual has the highest priority: it can preempt any active trigger
    (SCHEDULE, PROFILE/AUTO, AI) when the user explicitly commands the pump.
    """
    desired: Optional[bool] = None

    if state.zone_cfg.manual_pump_on is not None:
        desired = state.zone_cfg.manual_pump_on

    feed_desired = poll_manual_command_from_feed()
    if feed_desired is not None:
        desired = feed_desired

    if desired is None:
        return

    desired_value = 1 if desired else 0

    # Preempt any active non-manual trigger when the user explicitly wants ON
    if desired and state.pump_is_on and state.active_trigger != "MANUAL":
        print(f"[MANUAL] Overriding active trigger '{state.active_trigger}' — taking manual control")
        # Stop the current irrigation cleanly (records event, clears state)
        stop_irrigation("manual override", started_ts=state.current_watering_started_at, force=True)
        # Now fall through to the start block below (pump_is_on will be False after stop)

    if state.last_manual_command == desired_value and state.pump_is_on == desired:
        return

    if desired and not state.pump_is_on:
        state.active_trigger = "MANUAL"
        state.current_watering_started_at = time.time()
        state.current_schedule_end_at = None
        state.current_schedule_slot_id = None
        state.suppress_device_audit = False
        state.profile_min_end_at = None
        state.stop_above_count = 0
        send_pump_command(1)
        # Set grace window so stale PUMP=0 telemetry from the ESP32 (arriving
        # before it has processed the ON command) does not immediately trigger
        # stop_irrigation("pump telemetry off"). Same guard used by start_irrigation().
        state.ignore_pump_off_until = time.time() + PUMP_OFF_GRACE_SEC
        state.last_manual_command_at = time.time()
        state.pending_manual_state = 1
        state.last_manual_feed_value = 1
        print("[MANUAL] Pump ON requested from web")
    elif (not desired) and state.pump_is_on:
        # For gateway-controlled sessions (SCHEDULE / PROFILE / AI) only honour a
        # manual OFF if the feed value is FRESH (user pressed it recently).
        # A stale cached OFF (e.g. pressed yesterday) must not kill today's schedule.
        # MANUAL sessions are always stoppable regardless of feed age.
        feed_is_fresh = state.last_manual_feed_age_sec <= MANUAL_FEED_STALE_SEC
        if state.active_trigger != "MANUAL" and not feed_is_fresh:
            print(
                f"[MANUAL] Ignoring stale OFF command "
                f"(feed age={int(state.last_manual_feed_age_sec)}s > {MANUAL_FEED_STALE_SEC}s) "
                f"while {state.active_trigger} is active"
            )
            return
        started_ts = state.current_watering_started_at
        stop_irrigation("manual command off", started_ts=started_ts, force=True)
        state.last_manual_command_at = time.time()
        state.pending_manual_state = 0
        state.last_manual_feed_value = 0
        print("[MANUAL] Pump OFF requested from web")

    state.last_manual_command = desired_value
    if state.pending_manual_state is None or state.pending_manual_state != desired_value:
        state.last_manual_command_at = time.time()
        state.pending_manual_state = desired_value

def run_auto_logic():
    if state.zone_cfg.profile.mode != "AUTO":
        return
    if state.latest_data is None:
        return

    # Debug: show current time and number of configured slots (helps diagnose missed triggers)
    try:
        print(f"[DEBUG] run_auto_logic: hhmm={hhmm_now()} slots={len(state.zone_cfg.time_slots)} mode={state.zone_cfg.profile.mode}")
    except Exception:
        pass

    soil = safe_int(state.latest_data.get("SOIL"), 0)
    min_soil = state.zone_cfg.profile.min_soil
    max_soil = state.zone_cfg.profile.max_soil
    stop_target = midpoint(min_soil, max_soil)

    # schedule handling moved to `run_schedule_logic()` called from main loop

    if soil <= min_soil and not state.pump_is_on:
        start_irrigation("PROFILE")

    # Stop PROFILE irrigation as soon as soil reaches the profile max threshold.
    # Defaults are intentionally immediate now: PROFILE_MIN_RUN_SEC=0 and STOP_HYSTERESIS_COUNT=1.
    if state.pump_is_on and state.active_trigger == "PROFILE":
        now_ts = time.time()
        min_end = state.profile_min_end_at or 0
        if now_ts >= min_end:
            if soil >= stop_target:
                state.stop_above_count = state.stop_above_count + 1
                try:
                    print(f"[DEBUG] PROFILE stop check {state.stop_above_count}/{STOP_HYSTERESIS_COUNT} (soil={soil} max={stop_target})")
                except Exception:
                    pass
                if state.stop_above_count >= STOP_HYSTERESIS_COUNT:
                    stop_irrigation(f"soil reached profile max threshold {stop_target}%")
            else:
                state.stop_above_count = 0

    # if pump is on but trigger is not PROFILE (e.g., DEVICE/manual), keep previous behavior
    if state.pump_is_on and state.active_trigger not in ("PROFILE", "SCHEDULE") and soil >= min_soil:
        stop_irrigation(f"soil reached midpoint target {min_soil}%")

    # In AUTO mode, let soil safety override a scheduled irrigation if the soil is already wet enough.
    if state.pump_is_on and state.active_trigger == "SCHEDULE":
        if soil >= max_soil:
            print(f"[AUTO OVERRIDE] soil={soil} >= max={max_soil}; stopping scheduled irrigation")
            stop_irrigation(f"auto override: soil reached profile max threshold {max_soil}%")
            return

    if (
        state.pump_is_on
        and state.active_trigger == "SCHEDULE"
        and state.current_schedule_end_at is not None
        and time.time() >= state.current_schedule_end_at
    ):
        stop_irrigation("schedule duration completed")

def run_ai_logic():
    """AI mode: call irrigation AI API every hour or when soil < threshold.

    The AI response returns a scheduled_at time and duration_seconds.
    The pump starts at that time and the irrigation event is recorded with actor='AI'.
    """
    if state.zone_cfg.profile.mode != "AI":
        return
    if state.latest_data is None:
        return

    soil = safe_int(state.latest_data.get("SOIL"), 0)
    min_soil = state.zone_cfg.profile.min_soil
    now_ts = time.time()

    time_since_last_call = now_ts - state.last_ai_call_time
    should_call_hourly = time_since_last_call >= AI_CALL_INTERVAL_SEC
    # Call on threshold breach only when no schedule is already pending
    should_call_threshold = (
        soil < min_soil
        and state.ai_scheduled_start is None
        and not state.pump_is_on
    )

    if (should_call_hourly or should_call_threshold) and not state.pump_is_on:
        try:
            print(
                f"[AI] Calling AI irrigation API (soil={soil}%, min={min_soil}%, "
                f"interval={int(time_since_last_call)}s, threshold_breach={should_call_threshold})"
            )
            result = backend.call_ai_irrigation(state.zone_cfg.zone_id, AI_LAT, AI_LON)
            state.last_ai_call_time = now_ts  # update regardless to avoid hammering on failure
            if result is not None:
                scheduled_epoch, ai_dur_sec = result
                state.ai_scheduled_start = scheduled_epoch
                state.ai_duration_sec = ai_dur_sec
                scheduled_str = datetime.fromtimestamp(scheduled_epoch).strftime("%Y-%m-%d %H:%M:%S")
                print(f"[AI] Irrigation scheduled at {scheduled_str} for {ai_dur_sec}s")
                publish_audit_log(
                    zone_id=state.zone_cfg.zone_id,
                    zone_name=state.zone_cfg.zone_name,
                    severity="INFO",
                    alert_type="IRRIGATION_EVENT",
                    actor="AI",
                    message=(
                        f"AI irrigation scheduled: starts at {scheduled_str}, "
                        f"duration {ai_dur_sec}s"
                    ),
                )
            else:
                print("[AI] AI API returned no schedulable result")
        except Exception as exc:
            print("AI irrigation API error:", exc)
            state.last_ai_call_time = now_ts

    # Start the AI-scheduled pump when the scheduled time arrives
    if (
        state.ai_scheduled_start is not None
        and not state.pump_is_on
        and now_ts >= state.ai_scheduled_start
    ):
        dur = state.ai_duration_sec or 60
        drift_ms = int((now_ts - state.ai_scheduled_start) * 1000)
        print(f"[AI] Starting AI-scheduled irrigation, duration={dur}s, drift={drift_ms}ms")
        state.ai_scheduled_start = None
        state.ai_duration_sec = None
        start_irrigation("AI", dur, started_ts=now_ts)

    # Stop AI irrigation when its duration expires
    if (
        state.pump_is_on
        and state.active_trigger == "AI"
        and state.current_schedule_end_at is not None
        and now_ts >= state.current_schedule_end_at
    ):
        stop_irrigation("AI schedule duration completed", actor="AI")


def run_schedule_logic():
    """Trigger schedule with exact timing and exact planned stop time."""
    try:
        hit = check_schedule_trigger()
        if hit is None:
            return
        slot, scheduled_ts = hit
        if state.pump_is_on:
            current_priority = TRIGGER_PRIORITY.get(state.active_trigger or "", 0)
            if current_priority >= TRIGGER_PRIORITY.get("SCHEDULE", 0):
                print(f"[SCHEDULE] Ignoring scheduled slot {slot.slot_id}: higher/equal priority active ({state.active_trigger})")
                return
            # SCHEDULE can preempt lower-priority triggers via start_irrigation priority logic
        state.current_schedule_slot_id = slot.slot_id
        try:
            dur_sec = int(slot.duration)
        except Exception:
            dur_sec = slot.duration
        drift_ms = int((time.time() - scheduled_ts) * 1000)
        print(f"[SCHEDULE] Triggering slot {slot.slot_id} planned={datetime.fromtimestamp(scheduled_ts).strftime('%H:%M:%S')} drift_ms={drift_ms} duration={dur_sec}s")
        start_irrigation("SCHEDULE", dur_sec, started_ts=scheduled_ts)
    except Exception as exc:
        print("run_schedule_logic error:", exc)

# ==========================================================
# SERIAL
# ==========================================================
def parse_serial_line(line: str) -> Optional[Dict[str, Any]]:
    # extract the first telemetry segment that looks like '!...#' in case the
    # serial buffer contains other debug lines on the same read
    m = re.search(r"(![^#]*#)", line)
    if not m:
        return None

    seg = m.group(1)
    print("RAW:", seg)
    cleaned = seg.lstrip("!").rstrip("#")
    parts = cleaned.split(";")
    data: Dict[str, Any] = {}

    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        data[key] = value
    # parse available keys individually so partial updates are allowed
    result: Dict[str, Any] = {}
    try:
        # standard telemetry
        if "TEMP" in data:
            try:
                result["TEMP"] = float(data["TEMP"])
            except Exception:
                pass
        if "HUMI" in data:
            try:
                result["HUMI"] = float(data["HUMI"])
            except Exception:
                pass
        if "SOIL" in data:
            try:
                result["SOIL"] = int(data["SOIL"])
            except Exception:
                pass
        if "RAW" in data:
            try:
                result["RAW"] = int(data.get("RAW", 0))
            except Exception:
                pass
        if "PUMP" in data:
            try:
                result["PUMP"] = int(data["PUMP"])
            except Exception:
                pass

        # EVENT messages from device: TYPE=START|STOP, ZONE, ID, TS, START_TS, DUR
        if "TYPE" in data:
            etype = str(data.get("TYPE")).strip().upper()
            if etype in ("START", "STOP"):
                result["EVENT_TYPE"] = etype
                if "ZONE" in data:
                    result["EVENT_ZONE"] = str(data.get("ZONE"))
                if "ID" in data:
                    result["EVENT_ID"] = str(data.get("ID"))
                if "TS" in data:
                    try:
                        result["EVENT_TS"] = int(data.get("TS"))
                    except Exception:
                        pass
                if "START_TS" in data:
                    try:
                        result["EVENT_START_TS"] = int(data.get("START_TS"))
                    except Exception:
                        pass
                if "DUR" in data:
                    try:
                        result["EVENT_DUR"] = int(data.get("DUR"))
                    except Exception:
                        pass

        if not result:
            return None
        return result
    except Exception as exc:
        print("Parse error:", exc)
        return None

# ==========================================================
# ALERTS + TELEMETRY
# ==========================================================
def process_plant_alerts():
    if state.latest_data is None:
        return

    current_time = time.time()
    soil = safe_int(state.latest_data.get("SOIL"), 0)
    min_soil = state.zone_cfg.profile.min_soil

    if soil < min_soil and current_time - state.last_alert_time >= ALERT_INTERVAL_SEC:
        body = f"""He thong tuoi cay phat hien dat qua kho

Zone: {state.zone_cfg.zone_name or state.zone_cfg.zone_id}
Nhiet do: {state.latest_data['TEMP']} C
Do am khong khi: {state.latest_data['HUMI']} %
Do am dat: {soil} %
Nguong toi thieu: {min_soil} %
Trang thai bom: {state.latest_data['PUMP']}
Mode: {state.zone_cfg.profile.mode}
"""
        send_email("Canh bao: Dat kho", body)
        publish_audit_log(
            zone_id=state.zone_cfg.zone_id,
            zone_name=state.zone_cfg.zone_name,
            severity="WARNING",
            alert_type="PLANT_STATUS",
            actor="SYSTEM",
            message=f"Soil moisture alert: {soil}% is below min threshold {min_soil}%",
        )
        state.last_alert_time = current_time

def process_device_status():
    now_ts = time.time()
    for dev in DEVICE_KEYS:
        last_seen = state.device_last_seen.get(dev, 0)
        if last_seen == 0:
            # never seen yet
            continue
        offline_for = now_ts - last_seen
        if offline_for >= DEVICE_OFFLINE_SEC and not state.device_offline_logged.get(dev, False):
            publish_audit_log(
                zone_id=state.zone_cfg.zone_id,
                zone_name=state.zone_cfg.zone_name,
                severity="CRITICAL",
                alert_type="DEVICE_STATUS",
                actor="SYSTEM",
                message=f"{DEVICE_FRIENDLY.get(dev, dev)} offline: no telemetry received for {int(offline_for)} seconds from zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id}",
            )
            state.device_offline_logged[dev] = True


def send_to_adafruit_if_due():
    if state.latest_data is None:
        return
    now_ts = time.time()

    # PUMP is only published to Adafruit when an AUTO/SCHEDULE/AI pump event fires
    # (start or stop).  The flag is set exactly then and consumed once here.
    # Regular interval/change sends (TEMP/HUMI/SOIL) never carry PUMP.
    publish_pump_now = state.pump_feed_dirty

    # Change-detection: never trigger on PUMP so device telemetry PUMP changes
    # don't cause premature sends or Adafruit feedback loops.
    keys_to_check = ["TEMP", "HUMI", "SOIL", "PUMP"]
    keys_for_change = ["TEMP", "HUMI", "SOIL"]

    # detect change vs last sent data
    changed = False
    if SEND_IMMEDIATE_ON_CHANGE:
        for k in keys_for_change:
            if k in state.latest_data:
                prev = state.last_sent_data.get(k)
                curr = state.latest_data.get(k)
                if prev is None or str(prev) != str(curr):
                    changed = True
                    break

    # if nothing changed, no pump event, and interval hasn't elapsed, skip
    if (not changed) and (not publish_pump_now) and (now_ts - state.last_send_time < SEND_INTERVAL_SEC):
        return

    try:
        print("Sending to Adafruit...", "(changed)" if changed else "(pump event)" if publish_pump_now else "(interval)")
        if "TEMP" in state.latest_data:
            aio.send(FEED_TEMP, state.latest_data["TEMP"])
        if "HUMI" in state.latest_data:
            aio.send(FEED_HUM, state.latest_data["HUMI"])
        if "SOIL" in state.latest_data:
            aio.send(FEED_SOIL, state.latest_data["SOIL"])
        if publish_pump_now and "PUMP" in state.latest_data:
            aio.send(FEED_PUMP_STATE, state.latest_data["PUMP"])
            state.pump_feed_dirty = False  # consumed
        state.last_send_time = now_ts
        # snapshot last sent (always track PUMP for dedup even if not published)
        state.last_sent_data = {k: state.latest_data.get(k) for k in keys_to_check if k in state.latest_data}
        # After sending telemetry, update devices' last-active timestamps in backend
        try:
            devices_payload: Dict[str, str] = {}
            for dev in DEVICE_KEYS:
                ts = state.device_last_seen.get(dev) or state.last_send_time
                devices_payload[dev] = datetime.fromtimestamp(ts, UTC).isoformat().replace("+00:00", "Z")
            backend.update_devices_last_active(state.zone_cfg.zone_id, devices_payload)
        except Exception:
            # don't fail the main loop if updating last-active fails
            pass
        print("Send OK")
        print("===============")
    except ThrottlingError:
        print("Adafruit throttling: gui qua nhanh")
        time.sleep(5)
    except Exception as exc:
        print("Send error:", exc)
        time.sleep(0.5)


def handle_device_event(parsed: Dict[str, Any]) -> None:
    try:
        etype = parsed.get("EVENT_TYPE")
        ezone = parsed.get("EVENT_ZONE") or state.zone_cfg.zone_id
        eid = parsed.get("EVENT_ID")
        ets = parsed.get("EVENT_TS") or int(time.time())

        try:
            state.mark_device_seen("PUMP")
        except Exception:
            pass

        if etype == "START":
            state.pump_is_on = True
            state.current_watering_started_at = state.current_watering_started_at or ets
            state.current_schedule_slot_id = state.current_schedule_slot_id or eid
            # Only attribute to DEVICE and publish an audit when no gateway trigger is
            # already owning this irrigation session.  If MANUAL/SCHEDULE/PROFILE/AI is
            # active, the START echo from the device is pure confirmation — overwriting
            # active_trigger here would cause the preemption logic (run_manual_logic etc.)
            # to misfire on the very next loop iteration (stop → restart oscillation).
            if not state.active_trigger:
                state.active_trigger = "DEVICE"
                if not state.suppress_device_audit:
                    publish_audit_log(
                        zone_id=state.zone_cfg.zone_id,
                        zone_name=state.zone_cfg.zone_name,
                        severity="INFO",
                        alert_type="IRRIGATION_EVENT",
                        actor="DEVICE",
                        message=json.dumps({"event": "start", "zone": ezone, "id": eid, "ts": ets}, ensure_ascii=False),
                    )

        elif etype == "STOP":
            start_ts = parsed.get("EVENT_START_TS") or state.current_watering_started_at or (ets - (parsed.get("EVENT_DUR") or 0))
            if state.suppress_device_audit:
                state.current_watering_started_at = start_ts
                stop_irrigation("device reported stop")
            else:
                end_ts = ets
                duration_sec = max(0, int(end_ts - (start_ts or end_ts)))
                try:
                    backend.create_irrigation_event(
                        zone_id=ezone or state.zone_cfg.zone_id,
                        start_time=datetime.fromtimestamp(start_ts or end_ts, UTC).isoformat().replace("+00:00", "Z"),
                        end_time=datetime.fromtimestamp(end_ts, UTC).isoformat().replace("+00:00", "Z"),
                        duration=duration_sec,
                    )
                except Exception as exc:
                    print("Create irrigation event from device error:", exc)

                publish_audit_log(
                    zone_id=state.zone_cfg.zone_id,
                    zone_name=state.zone_cfg.zone_name,
                    severity="INFO",
                    alert_type="IRRIGATION_EVENT",
                    actor="DEVICE",
                    message=json.dumps({
                        "startTime": datetime.fromtimestamp(start_ts or end_ts, UTC).isoformat().replace("+00:00", "Z"),
                        "endTime": datetime.fromtimestamp(end_ts, UTC).isoformat().replace("+00:00", "Z"),
                        "duration": duration_sec,
                    }, ensure_ascii=False),
                )

                state.pump_is_on = False
                state.current_watering_started_at = None
                state.current_schedule_slot_id = None
                state.active_trigger = None
    except Exception as exc:
        print("Handle device event error:", exc)


def apply_parsed_telemetry(parsed: Dict[str, Any], prev_pump_state: bool) -> bool:
    telemetry_updated = False

    if state.latest_data is None:
        state.latest_data = {}

    for k, v in parsed.items():
        state.latest_data[k] = v
        if k in DEVICE_KEYS:
            try:
                state.mark_device_seen(k)
            except Exception:
                pass

    if "PUMP" in parsed:
        state.pump_is_on = parsed["PUMP"] == 1
        if state.pending_manual_state is not None and int(parsed["PUMP"]) == int(state.pending_manual_state):
            state.pending_manual_state = None
        telemetry_updated = True

    try:
        if "RAW" in parsed and COMPUTE_SOIL_FROM_RAW:
            raw_val = int(parsed.get("RAW") or 0)
            if SOIL_RAW_WET != SOIL_RAW_DRY:
                pct = int(round((raw_val - SOIL_RAW_DRY) * 100.0 / (SOIL_RAW_WET - SOIL_RAW_DRY)))
                if pct < 0:
                    pct = 0
                if pct > 100:
                    pct = 100
                state.latest_data["SOIL"] = pct
                telemetry_updated = True
                print(f"[DEBUG] Computed SOIL from RAW: {raw_val} -> {pct} (dry={SOIL_RAW_DRY},wet={SOIL_RAW_WET})")
    except Exception:
        pass

    if "EVENT_TYPE" in parsed:
        handle_device_event(parsed)

    try:
        if "PUMP" in parsed:
            new_pump = parsed.get("PUMP") == 1
            if prev_pump_state and (not new_pump) and not (parsed.get("EVENT_TYPE") == "STOP"):
                now_ts = time.time()
                if state.suppress_device_audit or now_ts < (state.ignore_pump_off_until or 0):
                    print("[DEBUG] Ignoring pump telemetry OFF due to gateway-initiated irrigation (suppression active or within grace window)")
                else:
                    start_ts = parsed.get("EVENT_START_TS") or state.current_watering_started_at
                    try:
                        stop_irrigation("pump telemetry off", started_ts=start_ts)
                    except Exception as exc:
                        print("Error stopping irrigation from pump telemetry:", exc)
    except Exception:
        pass

    if any(k in parsed for k in ("TEMP", "HUMI", "SOIL", "RAW", "PUMP")):
        telemetry_updated = True

    if telemetry_updated:
        print("Temp:", state.latest_data.get("TEMP"))
        print("Hum:", state.latest_data.get("HUMI"))
        print("Soil:", state.latest_data.get("SOIL"))
        print("Pump:", state.latest_data.get("PUMP"))
        print("--------------")
        process_plant_alerts()

    return telemetry_updated


while True:

    latest_parsed_telemetry: Optional[Dict[str, Any]] = None
    latest_prev_pump_state = state.pump_is_on

    while ser.in_waiting > 0:
        prev_pump_state_for_line = state.pump_is_on
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue

        parsed = parse_serial_line(line)
        if parsed is None:
            continue

        if "EVENT_TYPE" in parsed:
            apply_parsed_telemetry(parsed, prev_pump_state_for_line)
            continue

        if any(k in parsed for k in ("TEMP", "HUMI", "SOIL", "RAW", "PUMP")):
            latest_parsed_telemetry = parsed
            latest_prev_pump_state = prev_pump_state_for_line

    if latest_parsed_telemetry is not None:
        telemetry_changed = apply_parsed_telemetry(latest_parsed_telemetry, latest_prev_pump_state)
        if telemetry_changed:
            send_to_adafruit_if_due()

    process_device_status()

    try:
        run_schedule_logic()
    except Exception:
        pass

    # Manual control always runs first — highest priority, overrides all modes.
    run_manual_logic()

    mode = state.zone_cfg.profile.mode
    if mode == "AUTO":
        # Only run auto logic if pump is not already under manual control
        if state.active_trigger != "MANUAL":
            run_auto_logic()
    elif mode == "AI":
        # Only run AI logic if pump is not already under manual control
        if state.active_trigger != "MANUAL":
            run_ai_logic()

    try:
        if (
            state.pump_is_on
            and state.active_trigger in ("SCHEDULE", "AI")
            and state.current_schedule_end_at is not None
            and time.time() >= state.current_schedule_end_at
        ):
            trigger_actor = "AI" if state.active_trigger == "AI" else "SYSTEM"
            stop_irrigation(
                f"{state.active_trigger.lower()} duration completed (gateway timer)",
                actor=trigger_actor,
            )
    except Exception:
        pass

    # Keep blocking backend refresh after real-time control so schedule on/off is not delayed by HTTP.
    refresh_zone_config()

    send_to_adafruit_if_due()
    time.sleep(0.02)
