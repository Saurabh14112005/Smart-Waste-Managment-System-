#include "esp_camera.h"
#include <WiFi.h>

// ==========================
// WIFI CONFIG
// ==========================
const char* ssid = "OPPO A31";
const char* password = "12345678";

// ==========================
// API CONFIG
// ==========================
const char* serverHost = "192.168.43.134";
const int   serverPort = 8000;
const char* serverPath = "/predict";

// ==========================
// CAMERA PINS (AI-THINKER)
// ==========================
#define PWDN_GPIO_NUM     32
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
  Serial.println();
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("ESP32-CAM IP: ");
  Serial.println(WiFi.localIP());

  // Configure Camera
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
  
  // Use lower resolution for faster AI processing & less memory
  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // Initialize Camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }
  Serial.println("Camera Ready!");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // 1. Take a picture
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      delay(5000);
      return;
    }
    Serial.printf("Picture taken! Size: %u bytes\n", fb->len);

    // 2. Upload to server
    WiFiClient client;
    Serial.print("Connecting to server ");
    Serial.println(serverHost);
    
    if (client.connect(serverHost, serverPort)) {
      String head = "--Boundary\r\nContent-Disposition: form-data; name=\"file\"; filename=\"waste.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n";
      String tail = "\r\n--Boundary--\r\n";
      
      uint32_t imageLen = fb->len;
      uint32_t totalLen = head.length() + imageLen + tail.length();
      
      // Send HTTP POST headers
      client.println(String("POST ") + serverPath + " HTTP/1.1");
      client.println(String("Host: ") + serverHost + ":" + String(serverPort));
      client.println("Content-Length: " + String(totalLen));
      client.println("Content-Type: multipart/form-data; boundary=Boundary");
      client.println("Connection: close");
      client.println();
      
      // Send Head
      client.print(head);
      
      // Send Image payload in chunks
      uint8_t *fbBuf = fb->buf;
      size_t fbLen = fb->len;
      for (size_t n = 0; n < fbLen; n += 1024) {
        if (n + 1024 < fbLen) {
          client.write(fbBuf, 1024);
          fbBuf += 1024;
        } else if (fbLen % 1024 > 0) {
          size_t remainder = fbLen % 1024;
          client.write(fbBuf, remainder);
        }
      }
      
      // Send Tail
      client.print(tail);
      
      // Read Server Response
      Serial.println("Waiting for server response...");
      while (client.connected()) {
        String line = client.readStringUntil('\n');
        if (line == "\r") {
          break; // Headers ended
        }
      }
      
      // Print Response Body
      String response = client.readStringUntil('\n');
      Serial.println("Server Response:");
      Serial.println(response);
      
      client.stop();
    } else {
      Serial.println("Failed to connect to server");
    }

    // 3. Return frame buffer
    esp_camera_fb_return(fb);
    
  } else {
    Serial.println("WiFi Disconnected!");
  }

  // Wait 15 seconds before taking the next picture
  delay(15000); 
}
