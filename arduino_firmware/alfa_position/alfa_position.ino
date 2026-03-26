#include "WiFi.h"
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <ESPmDNS.h> 

// --- CONFIGURATION ---
const char* ssid = "WIFI 2.4GHz NAME";
const char* password = "PASSWORD";
const char* host = "radar";             
const int server_port = 50000;
IPAddress serverIP;

// BLE configuration
int scanTime = 2.5; // 2500ms for Bluetooth
BLEScan* pBLEScan;

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[+] WiFi Connected");

  if (!MDNS.begin("alfa")) {
    Serial.println("Error mDNS");
  }

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); 
  pBLEScan->setActiveScan(true);
}

void loop() {
  String payload = "";
  payload += "ID:ALFA\n";

  // --- ROUND 1: WIFI (Routers) ---
  Serial.println("[*] Scanning WiFi...");
  int n = WiFi.scanNetworks();
  payload += "TYPE:WIFI\n";
  for (int i = 0; i < n; ++i) {
    payload += WiFi.SSID(i) + " | " + WiFi.BSSIDstr(i) + " | " + String(WiFi.RSSI(i)) + "dBm\n";
  }

  // --- ROUND 2: BLUETOOTH (Speakers, Wearables, IoT) ---
  Serial.println("[*] Scanning Bluetooth...");
  BLEScanResults foundDevices = *pBLEScan->start(scanTime, false);
  payload += "TYPE:BLE\n";
  for (int i = 0; i < foundDevices.getCount(); i++) {
    BLEAdvertisedDevice device = foundDevices.getDevice(i);
    payload += String(device.getName().c_str()) + " | " + String(device.getAddress().toString().c_str()) + " | " + String(device.getRSSI()) + "dBm\n";
  }
  pBLEScan->clearResults();

  if (WiFi.status() == WL_CONNECTED) {
    if (serverIP.toString() == "0.0.0.0" || serverIP.toString() == "(IP unset)") {
      serverIP = MDNS.queryHost(host);
    }

    if (serverIP.toString() != "0.0.0.0") {
      WiFiClient client;
      if (client.connect(serverIP, server_port)) {
        client.print(payload);
        client.stop();
        Serial.println("[ALFA] Radar data sent.");
      } else {
        serverIP = IPAddress(0,0,0,0);
      }
    }
  }

  delay(5000);
}