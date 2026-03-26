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

const int wireshark_port = 5555;        // Wireshark Port (UDP)
WiFiUDP udp;

void setup() {
  Serial.begin(115200);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  Serial.print("Connecting Beta to the Network...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[OK] Beta Online");

  if (!MDNS.begin("beta")) {
    Serial.println("Error mDNS");
  }
}

int scanTimeBT = 2.5; 
BLEScan* pBLEScan;

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    if (serverIP.toString() == "0.0.0.0" || serverIP.toString() == "(IP unset)") {
      serverIP = MDNS.queryHost(host);
    }

    if (serverIP.toString() != "0.0.0.0") {
      WiFiClient client;
      if (client.connect(serverIP, server_port)) {
        client.println("ID:BETA");
        
        int n = WiFi.scanNetworks();
        for (int i = 0; i < n; ++i) {
          client.println(WiFi.SSID(i) + " | " + WiFi.BSSIDstr(i) + " | " + String(WiFi.RSSI(i)) + "dBm");
        }

        BLEScanResults foundDevices = *pBLEScan->start(scanTimeBT, false);
        for (int i = 0; i < foundDevices.getCount(); i++) {
          BLEAdvertisedDevice device = foundDevices.getDevice(i);
          client.println(String(device.getName().c_str()) + " | " + String(device.getAddress().toString().c_str()) + " | " + String(device.getRSSI()) + "dBm");
        }
        pBLEScan->clearResults();
        client.stop();
        Serial.println("[BETA] Radar data sent.");
      } else {
        serverIP = IPAddress(0,0,0,0);
      }
    }
  }

  CaptureTrafficUDP();
  delay(5000); 
}

void CaptureTrafficUDP() {
}