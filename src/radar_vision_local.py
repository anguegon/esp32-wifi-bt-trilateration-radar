import cv2
import numpy as np
import os
import sys
from ultralytics import YOLO

# --- SILENCE OPENCV WARNINGS ---
# This prevents the camera's [WARN] and [ERROR] messages from appearing on the terminal.
os.environ['OPENCV_LOG_LEVEL'] = 'OFF'

# --- CONFIGURATION ---
model = YOLO('yolov8n.pt')

# 2. DEFINE THE CAMERA INDEX
cap = cv2.VideoCapture(0) 

# --- NEW CLEAN ERROR LOGIC ---
if not cap.isOpened():
    print("\033[1;34m[*] Waiting for external device connection...\033[0m")
    sys.exit(0) # We close this process silently if there is no camera.

# Technological classes: 0:person, 62:tv, 63:laptop, 67:cell phone
DEVICES = [0, 62, 63, 67]

def read_radar():
    # We use BASE_DIR to make it automatic, just like in the other scripts.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "detected_targets.txt")
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()
            if lines:
                return lines
    return []

print("[*] Starting Local Vision...")

cv2.namedWindow("AI Radar HUD", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AI Radar HUD", 1024, 768)

while True:
    ret, frame = cap.read()
    if not ret:
        # If the camera disconnects mid-run
        print("\033[1;33m[!] Camera disconnected. Waiting for device...\033[0m")
        break

    # Execute optimized AI
    results = model(frame, verbose=False, classes=DEVICES, imgsz=320)
    annotated_frame = results[0].plot()

    # --- FLOATING TACTICAL HUD ---
    lines = read_radar()
    
    if lines:
        y0, dy = 30, 25
        cv2.putText(annotated_frame, "RADAR LINK ACTIVE", (10, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # We filter to show only the lines that contain "http" (the detected targets)
        targets = [l for l in lines if "http" in l]
        for i, line in enumerate(targets[-5:]): 
            text = line.strip().split("|")[0] # We simplified the name for the HUD
            y = y0 + i * dy
            cv2.putText(annotated_frame, f">> {text}", (11, y+1), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            cv2.putText(annotated_frame, f">> {text}", (10, y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

    cv2.imshow("AI Radar HUD", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
