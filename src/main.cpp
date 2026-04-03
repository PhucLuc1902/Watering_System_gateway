#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

// PIN CONFIG
#define DHT_PIN 3
#define DHT_TYPE DHT11
#define SOIL_PIN 1
#define SDA_PIN 8
#define SCL_PIN 9
#define RELAY_PIN 4
#define LED_BLINKY 20

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
    for (int i = 0; i < 10; i++) {
      sum += analogRead(pin);
      delay(10);
    }

    raw = sum / 10;
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
    digitalWrite(pin, LOW);   
    state = true;
  }

  void off() {
    digitalWrite(pin, HIGH);  
    state = false;
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

    if (cmd.startsWith("!CMD=PUMP;VALUE=") && cmd.endsWith("#")) {
      String value = cmd.substring(16, cmd.length() - 1);

      if (value == "1") {
        remotePumpState = true;
        Serial.println("Remote pump -> ON");
      } else if (value == "0") {
        remotePumpState = false;
        Serial.println("Remote pump -> OFF");
      }
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
    dht->update();
    soil->update();

    if (!dht->isValid()) {
      display->show("DHT read error", "Check sensor");
      alertBlinkEnabled = true;
      return;
    }

    float temp = dht->getTemp();
    float hum = dht->getHum();
    int soilPercent = soil->getPercent();
    int soilRaw = soil->getRaw();

    if (remotePumpState) {
      pump->on();
    } else {
      pump->off();
    }

  
    alertBlinkEnabled = false;

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

    String out = "!TEMP=" + String(temp, 1);
    out += ";HUMI=" + String(hum, 1);
    out += ";SOIL=" + String(soilPercent);
    out += ";RAW=" + String(soilRaw);
    out += ";PUMP=" + String(pump->isOn() ? 1 : 0);
    out += "#";

    Serial.println(out);
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

  if (millis() - lastRead > 3000) {
    lastRead = millis();
    controller.run();
  }
}