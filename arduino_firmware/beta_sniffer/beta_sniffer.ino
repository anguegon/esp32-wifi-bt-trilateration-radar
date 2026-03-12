#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// --- WIFI AND NETWORK CONFIGURATION (Modify)---
const char* ssid = "NET NAME";
const char* password = "NET PASSWORD";
const char* server_ip = "192.168.X.X";
const int server_port = 50000;          // Radar Server Port
const int wireshark_port = 5555;        // Wireshark Port (UDP)

WiFiUDP udp;

void setup() {
  Serial.begin(115200);
  
  // 1. Connect the Radar to the Network
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  Serial.print("Connecting Beta to the Network...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[OK] Beta Online");
}

int scanTimeBT = 2.5; 
BLEScan* pBLEScan;

void loop() {
  // TASK 1: DUAL RADAR (WiFi + BT)
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    if (client.connect(server_ip, server_port)) {
      client.println("ID:BETA");
      
      // WiFi Scan
      int n = WiFi.scanNetworks();
      for (int i = 0; i < n; ++i) {
        client.println(WiFi.SSID(i) + " | " + WiFi.BSSIDstr(i) + " | " + String(WiFi.RSSI(i)) + "dBm");
      }

      // BT Scan (2.5s)
      BLEScanResults foundDevices = *pBLEScan->start(scanTimeBT, false);
      for (int i = 0; i < foundDevices.getCount(); i++) {
        BLEAdvertisedDevice device = foundDevices.getDevice(i);
        client.println(String(device.getName().c_str()) + " | " + String(device.getAddress().toString().c_str()) + " | " + String(device.getRSSI()) + "dBm");
      }
      pBLEScan->clearResults();
      client.stop();
      Serial.println("[BETA] Radar data sent.");
    }
  }

  // --- TASK 2: SNIFFER (Traffic capture for Wireshark) ---
  // Note: To capture traffic from other devices, the ESP32
  // briefly alternates to promiscuous mode.
  CaptureTrafficUDP();

  delay(5000); // Scan every 5 seconds
}

void CaptureTrafficUDP() {
  // We simulate the encapsulation of a frame for the UDP tunnel
  // In an advanced implementation, you would enable promiscuous mode here
  // For now, we send a "Keep-alive" command to Wireshark to verify the tunnel
  udp.beginPacket(server_ip, wireshark_port);
  udp.write((const uint8_t*)"BETA_SNIFFER_ACTIVE", 19);
  udp.endPacket();
}