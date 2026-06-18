#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"
#include <esp_task_wdt.h>
#include <ArduinoOTA.h>

// ==========================
// WIFI CONFIG
// ==========================
const char* ssid = "OPPO A31";
const char* password = "12345678";

// ==========================
// API CONFIG
// ==========================
const char* serverUrl = "http://192.168.43.134:8000/iot/update";

// ==========================
// PIN CONFIG
// ==========================
#define TRIG_PIN 14
#define ECHO_PIN 15
#define GAS_PIN 34

#define DHTPIN 12
#define DHTTYPE DHT11
// Change to DHT22 if using DHT22

DHT dht(DHTPIN, DHTTYPE);

// ==========================
// BIN CONFIG
// ==========================
const int BIN_HEIGHT_CM = 30;

// ==========================
// SETUP
// ==========================
void setup() {

  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  dht.begin();

  Serial.println("\n=================================");
  Serial.println("CleanCity AI Hardware Node");
  Serial.println("=================================");

  // WiFi Connect
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected!");
  Serial.print("ESP32-CAM IP: ");
  Serial.println(WiFi.localIP());

  esp_task_wdt_init(60, true);

  ArduinoOTA.setHostname("cleancity-bin-1");
  ArduinoOTA.onStart([]() { Serial.println("[OTA] Start"); });
  ArduinoOTA.onEnd([]() { Serial.println("[OTA] End"); });
  ArduinoOTA.onError([](ota_error_t e) { Serial.printf("[OTA] Error %u\n", e); });
  ArduinoOTA.begin();
  Serial.println("ArduinoOTA ready (same LAN as IDE for upload).");
}

// ==========================
// ULTRASONIC FUNCTION
// ==========================
float getDistanceCM() {

  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH);

  float distance = duration * 0.034 / 2;

  return distance;
}

// ==========================
// LOOP
// ==========================
void loop() {

  esp_task_wdt_reset();
  ArduinoOTA.handle();

  if (WiFi.status() == WL_CONNECTED) {

    // ==========================
    // READ ULTRASONIC
    // ==========================
    float distance = getDistanceCM();

    // Calculate Fill %
    int fillLevel = 100 - ((distance / BIN_HEIGHT_CM) * 100);

    fillLevel = constrain(fillLevel, 0, 100);

    // ==========================
    // READ GAS SENSOR
    // ==========================
    int gasRaw = analogRead(GAS_PIN);

    int gasLevel = map(gasRaw, 0, 4095, 0, 100);

    // ==========================
    // READ DHT
    // ==========================
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    // Check DHT
    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("DHT Sensor Error!");

      temperature = 0;
      humidity = 0;
    }

    // ==========================
    // BATTERY (ADC — wire voltage divider to GPIO35 or change pin)
    // ==========================
    int adcBat = analogRead(35);
    // 18650 Battery Max (4.2V) -> ~2.1V at pin = ADC ~2600
    // 18650 Battery Min (3.0V) -> ~1.5V at pin = ADC ~1860
    int battery = constrain(map(adcBat, 1860, 2600, 0, 100), 0, 100);

    // ==========================
    // JSON PAYLOAD
    // ==========================
    String jsonPayload = "{";
    jsonPayload += "\"bin_id\":1,";
    jsonPayload += "\"location\":\"Smart bin node 1\",";
    jsonPayload += "\"latitude\":23.2599,";
    jsonPayload += "\"longitude\":77.4126,";
    jsonPayload += "\"zone\":\"FIELD\",";
    jsonPayload += "\"fill_level\":" + String(fillLevel) + ",";
    jsonPayload += "\"gas_level\":" + String(gasLevel) + ",";
    jsonPayload += "\"temperature\":" + String(temperature) + ",";
    jsonPayload += "\"humidity\":" + String(humidity) + ",";
    jsonPayload += "\"battery\":" + String(battery);
    jsonPayload += "}";

    // ==========================
    // SEND HTTP REQUEST
    // ==========================
    HTTPClient http;

    http.begin(serverUrl);

    http.addHeader("Content-Type", "application/json");

    http.setTimeout(3000); // Changed to 3000 to prevent WDT crash

    Serial.println("\n=================================");
    Serial.println("Sending Sensor Telemetry...");
    Serial.println(jsonPayload);

    int httpResponseCode = http.POST(jsonPayload);

    Serial.print("HTTP Response Code: ");
    Serial.println(httpResponseCode);

    if (httpResponseCode > 0) {

      String response = http.getString();

      Serial.println("Server Response:");
      Serial.println(response);

    } else {

      Serial.println("Failed to send data.");
    }

    http.end();

  } else {

    Serial.println("WiFi Disconnected!");
  }

  delay(5000);
}