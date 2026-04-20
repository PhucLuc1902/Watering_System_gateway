#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>
#include <vector>

// PIN CONFIG
#define DHT_PIN 3
#define DHT_TYPE DHT11
#define SOIL_PIN 14
#define SDA_PIN 8
#define SCL_PIN 9
#define RELAY_PIN 4
#define LED_BLINKY 20

// Read intervals (ms)
#define SOIL_READ_MS 500      // soil sensor read interval
#define DHT_READ_MS 2000      // DHT sensor read interval (DHT11 min ~1s)
#define MAIN_LOOP_READ_MS 50  // faster controller loop for quicker gateway/manual response
// Keep LCD and serial telemetry print at a human-friendly rate
#define TELEMETRY_PRINT_MS 1000
#define LCD_UPDATE_MS 1000

// Set to 1 if your relay module is active-LOW (drive LOW to energize relay).
// Set to 0 if your relay module is active-HIGH (drive HIGH to energize relay).
#ifndef RELAY_ACTIVE_LOW
#define RELAY_ACTIVE_LOW 1
#endif

// INTERFACES
class ISensor {
public:
  virtual void begin() = 0;
  virtual void update() = 0;
};

class IDisplay {
public:
  virtual void begin() = 0;
  virtual void show(String l1, String l2) = 0;
};

class IDataFormatter {
public:
  virtual String format(float t, float h, int soil, bool pumpOn) = 0;
};

// DHT SENSOR
class DHTSensor : public ISensor {
private:
  DHT dht;
  float temperature = 0.0;
  float humidity = 0.0;
  bool valid = false;

public:
  DHTSensor(uint8_t pin, uint8_t type) : dht(pin, type) {}

  void begin() override {
    dht.begin();
  }

  void update() override {
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (isnan(h) || isnan(t)) {
      Serial.println("DHT error");
      valid = false;
      return;
    }

    humidity = h;
    temperature = t;
    valid = true;
  }

  float getTemp() { return temperature; }
  float getHum() { return humidity; }
  bool isValid() { return valid; }
};

// SOIL SENSOR
class SoilSensor : public ISensor {
private:
  int pin;
  int dryValue;
  int wetValue;
  int raw = 0;
  int percent = 0;

public:
  SoilSensor(int p, int dry, int wet) {
    pin = p;
    dryValue = dry;
    wetValue = wet;
  }

  void begin() override {
    analogReadResolution(12);
  }

  void update() override {
    long sum = 0;
    const int samples = 5;
    for (int i = 0; i < samples; i++) {
      sum += analogRead(pin);
      delay(5);
    }

    raw = sum / samples;
    percent = map(raw, dryValue, wetValue, 0, 100);
    percent = constrain(percent, 0, 100);
  }

  int getPercent() { return percent; }
  int getRaw() { return raw; }
};

// LCD DISPLAY
class LCDDisplay : public IDisplay {
private:
  LiquidCrystal_I2C lcd;

  String fit16(String s) {
    if (s.length() < 16) {
      while (s.length() < 16) s += " ";
    } else if (s.length() > 16) {
      s = s.substring(0, 16);
    }
    return s;
  }

public:
  LCDDisplay(uint8_t addr, uint8_t c, uint8_t r) : lcd(addr, c, r) {}

  void begin() override {
    Wire.begin(SDA_PIN, SCL_PIN);
    lcd.init();
    lcd.backlight();
  }

  void show(String l1, String l2) override {
    lcd.setCursor(0, 0);
    lcd.print(fit16(l1));
    lcd.setCursor(0, 1);
    lcd.print(fit16(l2));
  }
};

// RELAY PUMP
class PumpRelay {
private:
  int pin;
  bool state = false;

public:
  PumpRelay(int p) {
    pin = p;
  }

  void begin() {
    pinMode(pin, OUTPUT);
    off();
  }

  void on() {
    digitalWrite(pin, RELAY_ACTIVE_LOW ? LOW : HIGH);
    state = true;
    // debug: print actual pin level after commanding
    Serial.print("Relay pin after ON: ");
    Serial.println(digitalRead(pin) == HIGH ? "HIGH" : "LOW");
  }

  void off() {
    digitalWrite(pin, RELAY_ACTIVE_LOW ? HIGH : LOW);
    state = false;
    // debug: print actual pin level after commanding
    Serial.print("Relay pin after OFF: ");
    Serial.println(digitalRead(pin) == HIGH ? "HIGH" : "LOW");
  }

  bool isOn() {
    return state;
  }
};

// FORMATTER
class SerialFormatter : public IDataFormatter {
public:
  String format(float t, float h, int soil, bool pumpOn) override {
    String s = "!TEMP=" + String(t, 1);
    s += ";HUMI=" + String(h, 1);
    s += ";SOIL=" + String(soil);
    s += ";RAW=" + String(0);
    s += ";PUMP=" + String(pumpOn ? 1 : 0);
    s += "#";
    return s;
  }
};

// SYSTEM CONTROLLER
class SystemController {
private:
  DHTSensor *dht;
  SoilSensor *soil;
  PumpRelay *pump;
  IDisplay *display;
  IDataFormatter *formatter;

  bool lcdPage = false;
  bool remotePumpState = false;
  String serialBuffer = "";

  bool alertBlinkEnabled = false;
  bool ledState = false;
  unsigned long lastBlinkTime = 0;
  const unsigned long blinkInterval = 300;

  // sensor timers (ms)
  unsigned long lastSoilMs = 0;
  unsigned long lastDhtMs = 0;
  unsigned long lastTelemetryMs = 0;
  unsigned long lastLCDMs = 0;
  unsigned long nowMs = 0;

  
  struct ScheduleEvent {
    String id;
    unsigned long start_ts; 
    unsigned long duration_sec;
    String zoneId;
  };

  std::vector<ScheduleEvent> scheduleEvents;
  bool haveTime = false;
  unsigned long timeEpochSecAtSet = 0; 
  unsigned long lastMillisAtTimeSet = 0;
  String deviceZoneId = "";
  String currentActiveEventId = "";
  unsigned long currentActiveStartEpoch = 0;

  unsigned long currentEpochSec() {
    if (!haveTime) return 0;
    unsigned long delta = (millis() - lastMillisAtTimeSet) / 1000;
    return timeEpochSecAtSet + delta;
  }

public:
  SystemController(
    DHTSensor *d,
    SoilSensor *s,
    PumpRelay *p,
    IDisplay *disp,
    IDataFormatter *fmt)
  {
    dht = d;
    soil = s;
    pump = p;
    display = disp;
    formatter = fmt;
  }

  void begin() {
    Serial.begin(115200);

    pinMode(LED_BLINKY, OUTPUT);
    digitalWrite(LED_BLINKY, LOW);

    display->begin();
    dht->begin();
    soil->begin();
    pump->begin();
  }

  void processSerialCommand(String cmd) {
    cmd.trim();

    // Handle pump command
    if (cmd.startsWith("!CMD=PUMP;VALUE=") && cmd.endsWith("#")) {
      String value = cmd.substring(16, cmd.length() - 1);

      if (value == "1") {
        remotePumpState = true;
        Serial.println("Remote pump -> ON");
      } else if (value == "0") {
        remotePumpState = false;
        Serial.println("Remote pump -> OFF");
      }
      return;
    }

    // Handle time sync: !TIME=<epoch># (epoch seconds)
    if (cmd.startsWith("!TIME=") && cmd.endsWith("#")) {
      String value = cmd.substring(6, cmd.length() - 1);
      unsigned long epoch = (unsigned long) value.toInt();
      if (epoch > 1000000000UL) {
        timeEpochSecAtSet = epoch;
        lastMillisAtTimeSet = millis();
        haveTime = true;
        Serial.print("Time synced: ");
        Serial.println(epoch);
      }
      return;
    }

    // Handle absolute schedule event: !SCHEDABS;ZONE=...;ID=...;START_TS=...;DUR=...#
    if (cmd.startsWith("!SCHEDABS;") && cmd.endsWith("#")) {
      String body = cmd.substring(1, cmd.length() - 1); // remove leading ! and trailing #
      // body format: SCHEDABS;ID=...;START_TS=...;DUR=...
      int pos = 0;
      int nextPos = body.indexOf(';', pos);
      // skip header
      if (nextPos > 0) pos = nextPos + 1;
      String id = "";
      String zone = "";
      unsigned long start_ts = 0;
      unsigned long dur = 0;
      while (pos < (int)body.length()) {
        nextPos = body.indexOf(';', pos);
        String part;
        if (nextPos == -1) {
          part = body.substring(pos);
          pos = body.length();
        } else {
          part = body.substring(pos, nextPos);
          pos = nextPos + 1;
        }
        int eq = part.indexOf('=');
        if (eq == -1) continue;
        String k = part.substring(0, eq);
        String v = part.substring(eq + 1);
        if (k == "ID") id = v;
        else if (k == "ZONE") zone = v;
        else if (k == "START_TS") start_ts = (unsigned long)v.toInt();
        else if (k == "DUR") dur = (unsigned long)v.toInt();
      }

      if (start_ts > 0 && dur > 0) {
        ScheduleEvent ev;
        ev.id = id;
        ev.zoneId = zone;
        ev.start_ts = start_ts;
        ev.duration_sec = dur;
        // replace existing with same id
        bool replaced = false;
        for (size_t i = 0; i < scheduleEvents.size(); i++) {
          if (scheduleEvents[i].id == ev.id && scheduleEvents[i].zoneId == ev.zoneId) {
            scheduleEvents[i] = ev;
            replaced = true;
            break;
          }
        }
        if (!replaced) scheduleEvents.push_back(ev);
        Serial.print("Received scheduled event: ");
        Serial.print(ev.id);
        if (ev.zoneId.length() > 0) {
          Serial.print(" zone=");
          Serial.print(ev.zoneId);
        }
        Serial.print(" start=");
        Serial.print(ev.start_ts);
        Serial.print(" dur=");
        Serial.println(ev.duration_sec);
      }
      return;
    }

    // Set device zone id: !ZONE=<zoneid>#
    if (cmd.startsWith("!ZONE=") && cmd.endsWith("#")) {
      String z = cmd.substring(6, cmd.length() - 1);
      z.trim();
      if (z.length() > 0) {
        this->deviceZoneId = z;
        Serial.print("Device zone set to: ");
        Serial.println(this->deviceZoneId);
      }
      return;
    }
  }

  void readSerialCommand() {
    while (Serial.available()) {
      char c = Serial.read();
      serialBuffer += c;

      if (c == '#') {
        processSerialCommand(serialBuffer);
        serialBuffer = "";
      }
    }
  }

  void updateBlinky() {
    if (!alertBlinkEnabled) {
      digitalWrite(LED_BLINKY, LOW);
      ledState = false;
      return;
    }

    if (millis() - lastBlinkTime >= blinkInterval) {
      lastBlinkTime = millis();
      ledState = !ledState;
      digitalWrite(LED_BLINKY, ledState ? HIGH : LOW);
    }
  }

  void run() {
    nowMs = millis();
    bool soilUpdated = false;
    bool dhtUpdated = false;

    // update soil sensor at its own interval
    if (lastSoilMs == 0 || (nowMs - lastSoilMs) >= SOIL_READ_MS) {
      soil->update();
      lastSoilMs = nowMs;
      soilUpdated = true;
    }

    // update DHT at its (slower) interval to avoid sensor errors
    if (lastDhtMs == 0 || (nowMs - lastDhtMs) >= DHT_READ_MS) {
      dht->update();
      lastDhtMs = nowMs;
      dhtUpdated = true;
    }

    if (dhtUpdated && !dht->isValid()) {
      display->show("DHT read error", "Check sensor");
      alertBlinkEnabled = true;
      return;
    }

    float temp = dht->getTemp();
    float hum = dht->getHum();
    int soilPercent = soil->getPercent();
    int soilRaw = soil->getRaw();

    // Scheduling: check absolute schedule events pushed from gateway
    unsigned long nowEpoch = currentEpochSec();
    bool scheduledOn = false;
    String matchedEventId = "";
    unsigned long matchedEventStart = 0;
    unsigned long matchedEventDur = 0;
    if (haveTime && nowEpoch > 0) {
      // check for active events
      for (size_t i = 0; i < scheduleEvents.size(); i++) {
        // if deviceZoneId set, only consider events for this zone
        if (deviceZoneId.length() > 0 && scheduleEvents[i].zoneId.length() > 0 && scheduleEvents[i].zoneId != deviceZoneId) {
          continue;
        }
        unsigned long s = scheduleEvents[i].start_ts;
        unsigned long e = s + scheduleEvents[i].duration_sec;
        if (nowEpoch >= s && nowEpoch < e) {
          scheduledOn = true;
          matchedEventId = scheduleEvents[i].id;
          matchedEventStart = s;
          matchedEventDur = scheduleEvents[i].duration_sec;
          break;
        }
      }

      // purge expired events that ended in the past
      for (int i = (int)scheduleEvents.size() - 1; i >= 0; i--) {
        unsigned long e = scheduleEvents[i].start_ts + scheduleEvents[i].duration_sec;
        if (nowEpoch >= e + 60) { // remove 1 minute after end
          scheduleEvents.erase(scheduleEvents.begin() + i);
        }
      }
    }

    // decide desired pump state (schedule has priority)
    bool desiredOn = scheduledOn || remotePumpState;
    bool wasOn = pump->isOn();

    if (desiredOn && !wasOn) {
      // turning on
      pump->on();
      unsigned long ts = nowEpoch > 0 ? nowEpoch : 0;
      String zid = deviceZoneId;
      String id = matchedEventId;
      // record active event
      currentActiveEventId = id;
      currentActiveStartEpoch = ts;
      // send EVENT START
      String ev = "!EVENT;TYPE=START";
      if (zid.length() > 0) ev += ";ZONE=" + zid;
      if (id.length() > 0) ev += ";ID=" + id;
      ev += ";TS=" + String(ts) + "#";
      Serial.println(ev);
      Serial.print("");
    } else if (!desiredOn && wasOn) {
      // turning off
      pump->off();
      unsigned long ts = nowEpoch > 0 ? nowEpoch : 0;
      String zid = deviceZoneId;
      String id = currentActiveEventId.length() > 0 ? currentActiveEventId : matchedEventId;
      unsigned long start_ts = currentActiveStartEpoch ? currentActiveStartEpoch : matchedEventStart;
      // send EVENT STOP (include START_TS when known)
      String ev = "!EVENT;TYPE=STOP";
      if (zid.length() > 0) ev += ";ZONE=" + zid;
      if (id.length() > 0) ev += ";ID=" + id;
      if (ts > 0) ev += ";TS=" + String(ts);
      if (start_ts > 0) ev += ";START_TS=" + String(start_ts);
      ev += "#";
      Serial.println(ev);
      // clear active
      currentActiveEventId = "";
      currentActiveStartEpoch = 0;
    }

  
    alertBlinkEnabled = false;

    // update LCD at human-friendly interval only (keep user display same)
    if (lastLCDMs == 0 || (nowMs - lastLCDMs) >= LCD_UPDATE_MS) {
      if (!lcdPage) {
        display->show(
          "T:" + String(temp, 1) + "C H:" + String((int)hum) + "%",
          "Soil:" + String(soilPercent) + "%"
        );
      } else {
        display->show(
          "Pump:" + String(pump->isOn() ? "ON" : "OFF"),
          "Raw:" + String(soilRaw)
        );
      }
      lcdPage = !lcdPage;
      lastLCDMs = nowMs;
    }

    String out = "!TEMP=" + String(temp, 1);
    out += ";HUMI=" + String(hum, 1);
    out += ";SOIL=" + String(soilPercent);
    out += ";RAW=" + String(soilRaw);
    out += ";PUMP=" + String(pump->isOn() ? 1 : 0);
    // also include the raw relay pin level for debugging (HIGH/LOW)
    out += ";RELAY=" + String(digitalRead(RELAY_PIN));
    out += "#";

    // Emit telemetry at fixed interval to keep serial monitor stable, but allow
    // immediate emit when pump state changed.
    if (desiredOn != wasOn) {
      Serial.println(out);
      lastTelemetryMs = nowMs;
    } else if (lastTelemetryMs == 0 || (nowMs - lastTelemetryMs) >= TELEMETRY_PRINT_MS) {
      Serial.println(out);
      lastTelemetryMs = nowMs;
    }
  }
};

// OBJECTS
LCDDisplay lcd(0x27, 16, 2);
SerialFormatter formatter;

DHTSensor dht(DHT_PIN, DHT_TYPE);
SoilSensor soil(SOIL_PIN, 4095, 1200);
PumpRelay pump(RELAY_PIN);

SystemController controller(
  &dht,
  &soil,
  &pump,
  &lcd,
  &formatter
);

unsigned long lastRead = 0;

void setup() {
  controller.begin();
}

void loop() {
  controller.readSerialCommand();
  controller.updateBlinky();

  // run controller more frequently so soil updates reach gateway faster
  if (millis() - lastRead > MAIN_LOOP_READ_MS) {
    lastRead = millis();
    controller.run();
  }
}
