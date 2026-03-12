#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// --- CONFIGURATION ---
const char* ssid = "NET NAME";
const char* password = "NET PASSWORD";
const char* server_ip = "192.168.X.X";
const int server_port = 50000;

// --- BLUETOOTH VARIABLES ---
BLEScan* pBLEScan;
float scanTimeBT = 2.5; // Seconds

void setup() {
  Serial.begin(115200);
  
  // WiFi configuration
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting Gamma...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[OK] Gamma Online");

  // --- INITIALIZATION BT  ---
  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); 
  pBLEScan->setActiveScan(true);
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    
    if (client.connect(server_ip, server_port)) {
      client.println("ID:GAMMA");
      client.flush();
      
      // CYCLE 1: WIFI
      Serial.println("[GAMMA] Scanning WiFi...");
      int n = WiFi.scanNetworks();
      for (int i = 0; i < n; ++i) {
        String name = WiFi.SSID(i);
        if (name == "") name = "Hide";
        client.println(name + " | " + WiFi.BSSIDstr(i) + " | " + String(WiFi.RSSI(i)) + "dBm");
      }

      // CYCLE 2: BLUETOOTH (2.5 seconds)
      Serial.println("[GAMMA] Scanning BT...");
      BLEScanResults foundDevices = *pBLEScan->start(scanTimeBT, false);
      for (int i = 0; i < foundDevices.getCount(); i++) {
        BLEAdvertisedDevice device = foundDevices.getDevice(i);
        String bName = String(device.getName().c_str());
        if (bName == "") bName = "Disp_BT";
        
        client.println(bName + " | " + String(device.getAddress().toString().c_str()) + " | " + String(device.getRSSI()) + "dBm");
      }
      pBLEScan->clearResults(); // Important to avoid overloading the memory
      
      client.stop();
      Serial.println("[OK] Gamma data sent.");
    }
  }
  // Short pause to avoid overloading the processor
  delay(100); 
}