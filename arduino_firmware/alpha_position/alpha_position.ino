#include "WiFi.h"
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// WiFi configuration (Modify)
const char* ssid = "NET NAME";
const char* password = "NET PASSWORD";
const char* server_ip = "192.168.X.X"; 
const int server_port = 50000;

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

  // --- ROUND 3: SEND TO THE SERVER ---
  sendData(payload);

  delay(10000); // Wait 10 seconds until the next big cycle
}

void sendData(String data) {
  WiFiClient client;
  if (client.connect(server_ip, server_port)) {
    client.print(data);
    client.stop();
    Serial.println("[+] Data sent successfully.");
  } else {
    Serial.println("[!] Error: Could not connect to the Python server.");
  }
}