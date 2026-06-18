# 🛠️ NEUROX Hardware Setup: ESP32-CAM + Ultrasonic Sensor

This guide provides the Arduino code to turn your ESP32-CAM into an AI Vision node that also reports bin fill levels using an Ultrasonic sensor.

## 1. Arduino Code (ESP32-CAM)

Copy this code into your Arduino IDE. Make sure you have the ESP32 board library installed.

```cpp
#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

// --- CONFIGURATION ---
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

#define TRIG_PIN 13
#define ECHO_PIN 12
#define BIN_HEIGHT 30 // Height of your bin in cm

// Camera Pin Mapping (AI-Thinker)
#define PWDN_GPIO_NUM     32
#define CONF_PIN_NUM      0
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // Camera Config
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 12;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // Init Camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  // Connect WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("Camera Stream URL: http://");
  Serial.print(WiFi.localIP());
  Serial.println("/stream");
}

long getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH);
  return duration * 0.034 / 2;
}

void loop() {
  // Python app will handle the stream. 
  // You can send distance data over Serial or a custom HTTP endpoint.
  long dist = getDistance();
  Serial.print("Distance: "); Serial.println(dist);
  delay(1000);
}
```

## 2. Hardware Wiring Diagram

| ESP32-CAM Pin | Component Pin | Note |
| :--- | :--- | :--- |
| 5V | VCC (Ultrasonic) | Power |
| GND | GND (Ultrasonic) | Ground |
| GPIO 13 | Trig (Ultrasonic) | Trigger Pulse |
| GPIO 12 | Echo (Ultrasonic) | Echo Pulse |

## 3. Python Integration

In your `app.py`, use `cv2.VideoCapture("http://<ESP32_IP>:81/stream")` to capture live frames.
