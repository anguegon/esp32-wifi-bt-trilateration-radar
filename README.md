# ESP32 WiFi/BT Trilateration Radar System

A real-time indoor positioning system using three ESP32 nodes and trilateration to track devices based on signal strength (RSSI), combined with AI computer vision for an augmented reality tactical display.

## 📋 System Overview

Autonomous AI Radar & WiFi Trilateration System
This project implements a portable, real-time tracking system that combines:
- WiFi Trilateration using RSSI from ESP32 nodes
- YOLOv8 AI Computer Vision for object detection
- Tactical HUD overlay on live camera feed

The system runs entirely on a Raspberry Pi, acting as a standalone master node.

## 📡 1. Hardware & Network Requirements

### Frequency Limitation
- 2.4GHz Only: The system exclusively captures MAC addresses on the 2.4GHz band (due to ESP32 hardware limits)
- Required Network: You must have a dedicated 2.4GHz WiFi network where both ESP32 antennas and Raspberry Pi are connected

### ⚠️ Network Stability Warning
- Do NOT use Mobile Hotspots: While smartphones offer 2.4GHz hotspots, this is strongly discouraged. Every restart or reconnection changes IP addresses, requiring manual updates to SERVER_IP in both radar_server.py and ESP32 firmware
- Recommended Setup: Use a stable, always-on network like a WiFi repeater or dedicated router configured for the site.
- Note that the object recognition AI (YOLOv8) is around 10GB in size. The code can work perfectly well without the AI; it's only included if you want a slightly more immersive graphical interface with a Cyberpunk style.

## 📂 2. PROJECT STRUCTURE

To keep the project organized, we use the following directory layout:

```text
radar_project/
├── venv_radar/          # Python Virtual Environment
├── src/                 # Source Code Folder
│   ├── radar_main.py    # Master script
│   ├── radar_server.py  # Processing & Math engine
│   ├── radar_vision_local.py # Vision & HUD overlay
│   └── receptor_video.py # Experimental RPi receiver
├── README.md            # Documentation
└── requirements.txt     # Project dependencies

## 🛠️ 3. Environment Setup for AI (Optional) (Same for Raspberry Pi)

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

## 3. Core System Components

### A. The Master Controller (radar_main.py)
This script manages the entire system lifecycle, launching the server and HUD windows.

Launch command: python3 radar_main.py

import subprocess, os, time, sys, select

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv_radar/bin/python3")
SERVER_SCRIPT = os.path.join(BASE_DIR, "radar_server.py")
VISION_SCRIPT = os.path.join(BASE_DIR, "radar_vision_local.py")

def launch_service(name, cmd, new_window=True):
    print(f"[*] Starting {name}...")
    if new_window:
        return subprocess.Popen(f"xterm -T '{name}' -e '{' '.join(cmd)}; exec bash'", shell=True)
    return subprocess.Popen(cmd)

# Launching the system
processes = []
processes.append(launch_service("RADAR_SERVER", [VENV_PYTHON, SERVER_SCRIPT]))
time.sleep(2)  # Wait for socket
processes.append(launch_service("AI_VISION_HUD", [VENV_PYTHON, VISION_SCRIPT], False))

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    for p in processes:
        p.terminate()



### B. The Processing Server (radar_server.py)
Calculates coordinates and matches orientation with trilateration data.

# Key configuration variables:
LAT_ORIGIN, LON_ORIGIN = 0.0, 0.0  # Set your starting reference
SYSTEM_AZIMUTH = 180  # Set orientation (0:East, 90:North, 180:West, 270:South)
SERVER_IP = "192.168.1.XXX"  # Static IP of your Raspberry Pi



### C. ESP32 Firmware Configuration
Each ESP32 node needs to be configured with:

// Important settings in firmware:
const char* ssid = "YOUR_2.4GHz_NETWORK";
const char* password = "YOUR_PASSWORD";
const char* serverIP = "192.168.1.XXX";  // Raspberry Pi IP
const int serverPort = 8080;


## 🕶️ 4. Portability & Gaze Detection
The system is designed for mobile use. By running everything on the Raspberry Pi:

- Local Processing: No need for an external PC.
- First-Person View (FPV): The radar_vision_local.py script draws the detected devices (MACs) directly onto the video feed from a camera mounted on your head/glasses.
- Relative Positioning: By knowing your position via trilateration and your azimuth (heading), the system can calculate if a detected signal is in front of you or behind you.

## 🔒 5. Security & SSH
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
