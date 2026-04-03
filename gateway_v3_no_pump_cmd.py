import os
import time
import json
import serial
import requests
import smtplib
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from Adafruit_IO import Client, MQTTClient
from Adafruit_IO.errors import ThrottlingError

# Load environment variables from .env file
load_dotenv()

# ==========================================================
# CONFIG
# ==========================================================
AIO_USERNAME = os.getenv("AIO_USERNAME", "")
AIO_KEY = os.getenv("AIO_KEY", "")

FEED_TEMP = os.getenv("FEED_TEMP", "temperature")
FEED_HUM = os.getenv("FEED_HUM", "humidity")
FEED_SOIL = os.getenv("FEED_SOIL", "soil")
FEED_PUMP = os.getenv("FEED_PUMP", "pump")

SERIAL_PORT = os.getenv("SERIAL_PORT", "COM4")
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "115200"))

API_BASE_URL = os.getenv("API_BASE_URL", "")
ZONE_ID = os.getenv("ZONE_ID", "")
API_TOKEN = os.getenv("API_TOKEN", "")
CONFIG_REFRESH_SEC = int(os.getenv("CONFIG_REFRESH_SEC", "15"))
SEND_INTERVAL_SEC = int(os.getenv("SEND_INTERVAL_SEC", "10"))
ALERT_INTERVAL_SEC = int(os.getenv("ALERT_INTERVAL_SEC", "300"))
DEVICE_OFFLINE_SEC = int(os.getenv("DEVICE_OFFLINE_SEC", "30"))

# Email is optional
GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_RECEIVER = os.getenv("GMAIL_RECEIVER", "")

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
    return datetime.utcnow().isoformat() + "Z"

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
    mode: str = "MANUAL"  # AUTO | MANUAL | AI

@dataclass
class ZoneConfig:
    zone_id: str = ""
    zone_name: str = ""
    profile_id: Optional[str] = None
    schedule_id: Optional[str] = None
    profile: ZoneProfile = field(default_factory=ZoneProfile)
    schedule_name: str = ""
    time_slots: List[TimeSlot] = field(default_factory=list)

# ==========================================================
# BACKEND CLIENT
# ==========================================================
class BackendClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "x-api-key": token 
        })

    def _get(self, path: str) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}{path}", timeout=10)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = self.session.post(
            f"{self.base_url}{path}",
            data=json.dumps(payload),
            timeout=10,
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
                    start_time=str(slot.get("startTime", "06:00"))[:5],
                    duration=safe_int(slot.get("duration"), 0),
                    days=normalize_days(slot.get("days")),
                    schedule_id=str(slot.get("scheduleId", schedule_id or "")),
                )
            )

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
        )

    def create_alert(
        self,
        *,
        zone_id: Optional[str],
        message: str,
        severity: str,
        alert_type: str,
        actor: str,
    ) -> None:
        payload = {
            "type": alert_type,
            "actor": actor,
            "message": message,
            "severity": severity,
            "zoneId": zone_id,
        }
        try:
            self._post("/api/alerts", payload)
        except Exception as exc:
            print("Create alert error:", exc)

    def create_irrigation_event(
        self,
        *,
        zone_id: str,
        start_time: str,
        end_time: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> None:
        payload: Dict[str, Any] = {
            "zoneId": zone_id,
            "startTime": start_time,
        }
        if end_time is not None:
            payload["endTime"] = end_time
        if duration is not None:
            payload["duration"] = duration
        try:
            self._post("/api/irrigation-events", payload)
        except Exception as exc:
            print("Create irrigation event error:", exc)

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
        self.last_device_seen = 0.0

        self.manual_pump_command = 0
        self.pump_is_on = False

        self.active_trigger: Optional[str] = None  # MANUAL | PROFILE | SCHEDULE
        self.current_watering_started_at: Optional[float] = None
        self.current_schedule_end_at: Optional[float] = None
        self.current_schedule_slot_id: Optional[str] = None

        self.processed_schedule_marks: Dict[str, bool] = {}
        self.device_offline_logged = False

    def mark_device_seen(self):
        self.last_device_seen = time.time()
        if self.device_offline_logged:
            backend.create_alert(
                zone_id=self.zone_cfg.zone_id,
                message=f"Device for zone {self.zone_cfg.zone_name or self.zone_cfg.zone_id} is back online",
                severity="INFO",
                alert_type="DEVICE_STATUS",
                actor="SYSTEM",
            )
            self.device_offline_logged = False

# ==========================================================
# CLIENTS
# ==========================================================
aio = Client(AIO_USERNAME, AIO_KEY)
ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
backend = BackendClient(API_BASE_URL, API_TOKEN)
state = GatewayState(ZONE_ID)

print("Gateway started...")

# ==========================================================
# DEVICE COMMANDS
# ==========================================================
def send_pump_command(value: int):
    cmd = f"!CMD=PUMP;VALUE={value}#\n"
    ser.write(cmd.encode("utf-8"))
    state.pump_is_on = value == 1
    print("Sent to ESP32:", cmd.strip())

# ==========================================================
# IRRIGATION ACTIONS
# ==========================================================
def start_irrigation(trigger: str, duration_sec: Optional[int] = None):
    if state.pump_is_on:
        return

    send_pump_command(1)
    state.active_trigger = trigger
    state.current_watering_started_at = time.time()
    if trigger == "SCHEDULE" and duration_sec is not None:
        state.current_schedule_end_at = time.time() + duration_sec
    else:
        state.current_schedule_end_at = None

    zone_label = state.zone_cfg.zone_name or state.zone_cfg.zone_id
    soil = state.latest_data.get("SOIL") if state.latest_data else None
    detail = f", soil={soil}%" if soil is not None else ""
    backend.create_alert(
        zone_id=state.zone_cfg.zone_id,
        message=f"Irrigation started by {trigger} for zone {zone_label}{detail}",
        severity="INFO",
        alert_type="IRRIGATION_EVENT",
        actor="USER" if trigger == "MANUAL" else "SYSTEM",
    )

def stop_irrigation(reason: str):
    if not state.pump_is_on:
        return

    started_ts = state.current_watering_started_at or time.time()
    ended_ts = time.time()
    duration_sec = max(0, int(ended_ts - started_ts))

    send_pump_command(0)
    backend.create_irrigation_event(
        zone_id=state.zone_cfg.zone_id,
        start_time=datetime.utcfromtimestamp(started_ts).isoformat() + "Z",
        end_time=datetime.utcfromtimestamp(ended_ts).isoformat() + "Z",
        duration=duration_sec,
    )

    backend.create_alert(
        zone_id=state.zone_cfg.zone_id,
        message=f"Irrigation stopped: {reason}",
        severity="INFO",
        alert_type="IRRIGATION_EVENT",
        actor="SYSTEM",
    )

    state.active_trigger = None
    state.current_watering_started_at = None
    state.current_schedule_end_at = None
    state.current_schedule_slot_id = None

# ==========================================================
# ADAFRUIT MQTT (manual command only)
# ==========================================================
def connected(client):
    print("Connected to Adafruit MQTT")

def subscribe(client, userdata, mid, granted_qos):
    print("Subscribe successful")

def disconnected(client):
    print("Disconnected from Adafruit MQTT")
    backend.create_alert(
        zone_id=state.zone_cfg.zone_id,
        message="Gateway disconnected from Adafruit MQTT",
        severity="WARNING",
        alert_type="DEVICE_STATUS",
        actor="SYSTEM",
    )

def message(client, feed_id, payload):
    print(f"Receive from Adafruit -> {feed_id}: {payload}")
    return

    state.manual_pump_command = 1 if str(payload) == "1" else 0
    backend.create_alert(
        zone_id=state.zone_cfg.zone_id,
        message=f"Manual pump command received: {state.manual_pump_command}",
        severity="INFO",
        alert_type="IRRIGATION_EVENT",
        actor="USER",
    )

mqtt = MQTTClient(AIO_USERNAME, AIO_KEY)
mqtt.on_connect = connected
mqtt.on_disconnect = disconnected
mqtt.on_subscribe = subscribe
mqtt.on_message = message
mqtt.connect()
mqtt.loop_background()

# ==========================================================
# CONFIG REFRESH
# ==========================================================
def refresh_zone_config(force: bool = False):
    if not force and time.time() - state.last_config_refresh < CONFIG_REFRESH_SEC:
        return

    try:
        old_cfg = state.zone_cfg
        new_cfg = backend.fetch_zone_config(state.zone_id)
        state.zone_cfg = new_cfg
        state.last_config_refresh = time.time()

        print(
            f"Zone config refreshed -> zone={new_cfg.zone_name}, mode={new_cfg.profile.mode}, "
            f"min={new_cfg.profile.min_soil}, max={new_cfg.profile.max_soil}, slots={len(new_cfg.time_slots)}"
        )

        if old_cfg.profile.mode != new_cfg.profile.mode:
            backend.create_alert(
                zone_id=new_cfg.zone_id,
                message=f"Profile mode changed from {old_cfg.profile.mode} to {new_cfg.profile.mode}",
                severity="INFO",
                alert_type="DEVICE_STATUS",
                actor="SYSTEM",
            )

        if (
            old_cfg.profile.min_soil != new_cfg.profile.min_soil
            or old_cfg.profile.max_soil != new_cfg.profile.max_soil
        ):
            backend.create_alert(
                zone_id=new_cfg.zone_id,
                message=(
                    f"Profile thresholds updated: min={new_cfg.profile.min_soil}%, "
                    f"max={new_cfg.profile.max_soil}%"
                ),
                severity="INFO",
                alert_type="PLANT_STATUS",
                actor="SYSTEM",
            )

        old_schedule_sig = [
            (slot.slot_id, slot.start_time, tuple(slot.days), slot.duration)
            for slot in old_cfg.time_slots
        ]
        new_schedule_sig = [
            (slot.slot_id, slot.start_time, tuple(slot.days), slot.duration)
            for slot in new_cfg.time_slots
        ]
        if old_schedule_sig != new_schedule_sig:
            backend.create_alert(
                zone_id=new_cfg.zone_id,
                message=f"Schedule updated for zone {new_cfg.zone_name or new_cfg.zone_id}",
                severity="INFO",
                alert_type="IRRIGATION_EVENT",
                actor="SYSTEM",
            )

    except Exception as exc:
        print("Fetch zone config error:", exc)
        backend.create_alert(
            zone_id=state.zone_cfg.zone_id,
            message=f"Failed to refresh zone/profile/schedule config: {exc}",
            severity="WARNING",
            alert_type="DEVICE_STATUS",
            actor="SYSTEM",
        )

# ==========================================================
# MODE LOGIC
# ==========================================================
def run_manual_logic():
    if state.zone_cfg.profile.mode != "MANUAL":
        return

    if state.manual_pump_command == 1 and not state.pump_is_on:
        start_irrigation("MANUAL")
    elif state.manual_pump_command == 0 and state.pump_is_on:
        stop_irrigation("manual command OFF")

def check_schedule_trigger() -> Optional[TimeSlot]:
    current_hhmm = hhmm_now()
    current_day = weekday_name_now()
    today = datetime.now().strftime("%Y-%m-%d")

    for slot in state.zone_cfg.time_slots:
        if slot.start_time != current_hhmm:
            continue
        if slot.days and current_day not in slot.days:
            continue

        slot_key = slot.slot_id or f"{slot.start_time}-{slot.duration}-{','.join(slot.days)}"
        mark = f"{today}:{slot_key}"
        if state.processed_schedule_marks.get(mark):
            continue

        state.processed_schedule_marks[mark] = True
        return slot

    return None

def run_auto_logic():
    if state.zone_cfg.profile.mode != "AUTO":
        return
    if state.latest_data is None:
        return

    soil = safe_int(state.latest_data.get("SOIL"), 0)
    min_soil = state.zone_cfg.profile.min_soil
    max_soil = state.zone_cfg.profile.max_soil
    stop_target = midpoint(min_soil, max_soil)

    # Schedule first
    slot = check_schedule_trigger()
    if slot is not None and not state.pump_is_on:
        state.current_schedule_slot_id = slot.slot_id
        start_irrigation("SCHEDULE", slot.duration)
        backend.create_alert(
            zone_id=state.zone_cfg.zone_id,
            message=(
                f"Schedule triggered at {slot.start_time} for {slot.duration}s "
                f"on zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id}"
            ),
            severity="INFO",
            alert_type="IRRIGATION_EVENT",
            actor="SYSTEM",
        )

    # Threshold-based irrigation
    if soil <= min_soil and not state.pump_is_on:
        start_irrigation("PROFILE")
        backend.create_alert(
            zone_id=state.zone_cfg.zone_id,
            message=f"Soil moisture {soil}% <= min threshold {min_soil}%, profile irrigation started",
            severity="WARNING",
            alert_type="PLANT_STATUS",
            actor="SYSTEM",
        )

    # Stop conditions
    if state.pump_is_on and state.active_trigger == "PROFILE" and soil >= stop_target:
        stop_irrigation(f"soil reached midpoint target {stop_target}%")

    if (
        state.pump_is_on
        and state.active_trigger == "SCHEDULE"
        and state.current_schedule_end_at is not None
        and time.time() >= state.current_schedule_end_at
    ):
        stop_irrigation("schedule duration completed")

def run_ai_logic():
    # Reserved for future AI mode.
    return

# ==========================================================
# SERIAL
# ==========================================================
def parse_serial_line(line: str) -> Optional[Dict[str, Any]]:
    if not line.startswith("!"):
        return None

    print("RAW:", line)
    cleaned = line.replace("!", "").replace("#", "")
    parts = cleaned.split(";")
    data: Dict[str, Any] = {}

    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        data[key] = value

    try:
        return {
            "TEMP": float(data["TEMP"]),
            "HUMI": float(data["HUMI"]),
            "SOIL": int(data["SOIL"]),
            "RAW": int(data.get("RAW", 0)),
            "PUMP": int(data["PUMP"]),
        }
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
"""
        send_email("Canh bao: Dat kho", body)
        backend.create_alert(
            zone_id=state.zone_cfg.zone_id,
            message=f"Soil moisture alert: {soil}% is below min threshold {min_soil}%",
            severity="WARNING",
            alert_type="PLANT_STATUS",
            actor="SYSTEM",
        )
        state.last_alert_time = current_time

def process_device_status():
    if state.last_device_seen == 0:
        return

    offline_for = time.time() - state.last_device_seen
    if offline_for >= DEVICE_OFFLINE_SEC and not state.device_offline_logged:
        backend.create_alert(
            zone_id=state.zone_cfg.zone_id,
            message=(
                f"Device offline: no telemetry received for {int(offline_for)} seconds "
                f"from zone {state.zone_cfg.zone_name or state.zone_cfg.zone_id}"
            ),
            severity="CRITICAL",
            alert_type="DEVICE_STATUS",
            actor="SYSTEM",
        )
        state.device_offline_logged = True

def send_to_adafruit_if_due():
    if state.latest_data is None:
        return
    if time.time() - state.last_send_time < SEND_INTERVAL_SEC:
        return

    try:
        print("Sending to Adafruit...")
        aio.send(FEED_TEMP, state.latest_data["TEMP"])
        aio.send(FEED_HUM, state.latest_data["HUMI"])
        aio.send(FEED_SOIL, state.latest_data["SOIL"])
        aio.send(FEED_PUMP, state.latest_data["PUMP"])
        state.last_send_time = time.time()
        print("Send OK")
        print("===============")
    except ThrottlingError:
        print("Adafruit throttling: gui qua nhanh")
        time.sleep(5)
    except Exception as exc:
        print("Send error:", exc)
        time.sleep(3)

# ==========================================================
# MAIN
# ==========================================================
refresh_zone_config(force=True)
backend.create_alert(
    zone_id=state.zone_cfg.zone_id,
    message="Gateway started",
    severity="INFO",
    alert_type="DEVICE_STATUS",
    actor="SYSTEM",
)

while True:
    refresh_zone_config()

    line = ser.readline().decode(errors="ignore").strip()
    if line:
        parsed = parse_serial_line(line)
        if parsed is not None:
            state.latest_data = parsed
            state.mark_device_seen()
            state.pump_is_on = parsed["PUMP"] == 1
            print("Temp:", parsed["TEMP"])
            print("Hum:", parsed["HUMI"])
            print("Soil:", parsed["SOIL"])
            print("Pump:", parsed["PUMP"])
            print("--------------")
            process_plant_alerts()

    process_device_status()

    mode = state.zone_cfg.profile.mode
    if mode == "MANUAL":
        run_manual_logic()
    elif mode == "AUTO":
        run_auto_logic()
    elif mode == "AI":
        run_ai_logic()

    send_to_adafruit_if_due()
    time.sleep(1)