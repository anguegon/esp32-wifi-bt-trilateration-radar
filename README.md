# ESP32 WiFi/BT Trilateration Radar System

A real-time indoor positioning system using three ESP32 nodes and trilateration to track devices based on signal strength (RSSI), combined with AI computer vision for an augmented reality tactical display.

## 📋 System Overview

Autonomous AI Radar & WiFi Trilateration System
This project implements a portable, real-time tracking system that combines:
- WiFi Trilateration using RSSI from ESP32 nodes
- YOLOv8 AI Computer Vision for object detection
- Tactical HUD overlay on live camera feed

The system runs entirely on the PC on Linux or in a RPi5 with 8/16GB RAM, acting as a standalone master node.

## 📡 1. Hardware & Network Requirements

### Frequency Limitation
- 2.4GHz Only: The system exclusively captures MAC addresses on the 2.4GHz band (due to ESP32 hardware limits)
- Required Network: You must have a dedicated 2.4GHz WiFi network where both ESP32 antennas and PC/RPi are connected

### ⚠️ Network Stability Warning
- Do NOT use Mobile Hotspots: While smartphones offer 2.4GHz hotspots, this is strongly discouraged. Every restart or reconnection changes IP addresses, requiring manual updates to SERVER_IP in both radar_server.py and ESP32 firmware
- Recommended Setup: Use a stable, always-on network like a WiFi repeater or dedicated router configured for the site.
- Note that the object recognition AI (YOLOv8) is around 10GB in size. The code can work perfectly well without the AI; it's only included if you want a slightly more immersive graphical interface with a Cyberpunk style.

### Arduino IDE Configuration & Dependencies

To compile the firmware for the ESP32 nodes, you must configure your Arduino IDE correctly to handle the heavy network libraries:

#### Memory Partition (Mandatory)
Path: Tools -> Partition Scheme -> Huge APP (3MB No OTA/1MB SPIFFS).

Failure to set this will cause the firmware to crash due to memory overflow.

#### Required Dependencies
Install these from the Library Manager (Ctrl+Shift+I):

WiFi.h, BLEDevice.h, BLEUtils.h, BLEScan.h, BLEAdvertisedDevice.h (All standard core libraries for ESP32).

## 📂 2. PROJECT STRUCTURE

To keep the project organized, we use the following directory layout:

```text
radar_project/
├── venv_radar/                 # Python Virtual Environment for the AI
├── arduino_firmware/           # Arduino Code for the antennas
│   ├── alfa_position/     
│   │   └── alfa_position.ino   # Origin antenna (0,0)
│   ├── beta_sniffer/
│   │   └──beta_sniffer.ino     # This antenna defines the X-axis
│   └── gamma_satellite/      
│       └── gamma_satellite.ino # This antenna provides the third point of reference.
├── src/                        # Source Code Folder
│   ├── radar_main.py           # Master script
│   ├── radar_server.py         # Processing & Math engine
│   ├── radar_vision_local.py   # Vision & HUD overlay
│   └── receptor_video.py       # Experimental RPi receiver
├── README.md                   # Documentation
└── requirements.txt            # Project dependencies

## ⚙️ 3. Configuration Guide (You have to MODIFY the data in order to match you)
You must sync your network and geometric data across the system:

### A. Arduino Firmware (ESP32)
Update these constants in your .ino files:

ssid / password: Your WiFi credentials.

server_ip: The static IP address of your PC/RPi.

### B. Server Logic (radar_server.py)
Edit the following for accurate position calculation:

LAT_ORIGIN / LON_ORIGIN: GPS coordinates of your ALPHA antenna.

AZIMUTH_SISTEMA: Define the system heading (0° East, 90° North, 180° West, 270° South).

POSICIONES_ANTENAS: Define distances in meters relative to ALPHA (0,0).

## ⚙️ 4. Core System Components (You have to MODIFY the data in order to match you)

### A. The Master Controller (radar_main.py)
This script manages the entire system lifecycle, launching the server and HUD windows.

# Launch command: sudo python3 radar_main.py

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv_radar/bin/python3")
SERVER_SCRIPT = os.path.join(BASE_DIR, "radar_server.py")
VISION_SCRIPT = os.path.join(BASE_DIR, "radar_vision_local.py")

### B. The Processing Server (radar_server.py)
Calculates coordinates and matches orientation with trilateration data.

# Key configuration variables:
LAT_ORIGIN, LON_ORIGIN = 0.0, 0.0  # Set your starting reference
SYSTEM_AZIMUTH = 180  # Set orientation (0:East, 90:North, 180:West, 270:South)
SERVER_IP = "192.168.1.XXX"  # Static IP of your PC/RPi, use "ifconfig" on the cmd to see the WiFi LAN IP



### C. ESP32 Firmware Configuration
Each ESP32 node needs to be configured with:

// Important settings in firmware:
const char* ssid = "YOUR_2.4GHz_NETWORK";
const char* password = "YOUR_PASSWORD";
const char* serverIP = "192.168.1.X.X";  # OS IP (you can see that using the command "ipconfig" on windows or "ifconfig" on Linux cmd) 
const int serverPort = 8080;

## 📡 5. Technical Specifications of Antenna Nodes
The system uses three ESP32 nodes, each programmed with a unique specialized firmware to balance network scanning and traffic analysis.

### ALFA (Position Master & Data Aggregator)
Role: Central node for the antenna array.

Technical Function: It defines the Coordinate Origin (0,0). While scanning its own environment for WiFi and BLE devices, it also acts as the primary synchronization point. It ensures the relative distances to Beta and Gamma are correctly mapped before relaying the collective data to the Python Server.

Hardware Task: Dual-band scanning (WiFi + Bluetooth Low Energy).

### BETA (The Sniffer / Traffic Analyzer)
Role: Network security and traffic interception.

Technical Function: Beyond its role in trilateration (defining the X-axis), Beta operates in Promiscuous Mode. This allows it to intercept, log, and analyze network packets in real-time. It doesn't just see that a device exists; it captures raw traffic (packets) that are not necessarily addressed to it, making it essential for deep signal analysis and network monitoring.

Hardware Task: Packet injection/capture and dual-mode scanning.

### GAMMA (The Satellite / Triangulator)
Role: Geometric support and signal validation.

Technical Function: Gamma serves as the third vertex of the trilateration triangle. Its primary purpose is to provide a third Distance-to-Target (RSSI) measurement. By having this third point, the Python Server can solve the mathematical ambiguity of 2D positioning, pinpointing exactly where a MAC address is located instead of having two possible mirror locations.

Hardware Task: Constant environment scanning and remote reporting to the master node.


## 🛠️ 6. Environment Setup for AI (Optional) (Same for Raspberry Pi)

### Create the Virtual Environment

# 1. Navigate to the project folder
cd ~/radar_project

# 2. Create and activate the environment
python3 -m venv venv_radar
source venv_radar/bin/activate

# 3. Install dependencies
pip install ultralytics opencv-python numpy



### Download the AI Model
The first time you run the vision script, it will automatically download yolov8n.pt (Nano version), optimized for Raspberry Pi's CPU/GPU.

## 🕶️ 7. Portability & Gaze Detection
The system is designed for mobile use. By running everything on the Raspberry Pi 5:

- Local Processing: No need for an external PC.
- First-Person View (FPV): The radar_vision_local.py script draws the detected devices (MACs) directly onto the video feed from a camera mounted on your head/glasses.
- Relative Positioning: By knowing your position via trilateration and your azimuth (heading), the system can calculate if a detected signal is in front of you or behind you.

## 🔒 8. Security & SSH
If you need to manage the Raspberry Pi remotely from another laptop while it's "in the field":

1. Generate keys:

bash
ssh-keygen -t rsa

2. Copy to RPi:

bash
ssh-copy-id pi@

3. Connect:

bash
ssh pi@

*(No password required)*
