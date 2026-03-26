#include <WiFi.h>
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

BLEScan* pBLEScan;
float scanTimeBT = 2.5; 

void setup() {
  Serial.begin(115200);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting Gamma...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[OK] Gamma Online");

  if (!MDNS.begin("gamma")) {
    Serial.println("Error mDNS");
  }

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); 
  pBLEScan->setActiveScan(true);
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    if (serverIP.toString() == "0.0.0.0" || serverIP.toString() == "(IP unset)") {
      serverIP = MDNS.queryHost(host);
    }

    if (serverIP.toString() != "0.0.0.0") {
      WiFiClient client;
      
      if (client.connect(serverIP, server_port)) {
        client.println("ID:GAMMA");
        client.flush();
        
        Serial.println("[GAMMA] Scanning WiFi...");
        int n = WiFi.scanNetworks();
        for (int i = 0; i < n; ++i) {
          String name = WiFi.SSID(i);
          if (name == "") name = "Hide";
          client.println(name + " | " + WiFi.BSSIDstr(i) + " | " + String(WiFi.RSSI(i)) + "dBm");
        }

        Serial.println("[GAMMA] Scanning BT...");
        BLEScanResults foundDevices = *pBLEScan->start(scanTimeBT, false);
        for (int i = 0; i < foundDevices.getCount(); i++) {
          BLEAdvertisedDevice device = foundDevices.getDevice(i);
          String bName = String(device.getName().c_str());
          if (bName == "") bName = "Disp_BT";
          
          client.println(bName + " | " + String(device.getAddress().toString().c_str()) + " | " + String(device.getRSSI()) + "dBm");
        }
        pBLEScan->clearResults();
        client.stop();
        Serial.println("[GAMMA] Radar data sent.");
      } else {
        serverIP = IPAddress(0,0,0,0);
      }
    }
  }
  delay(5000); 
}