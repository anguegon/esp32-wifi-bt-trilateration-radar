import cv2
import numpy as np
import os
from ultralytics import YOLO

# --- CONFIGURATION ---
# 1. Load the YOLOv8 model
model = YOLO('yolov8n.pt')

# 2. DEFINE THE CAMERA INDEX (Where the X goes)
# Try with 0, if it doesn't work, try 2 (common in Pixart cameras)
cap = cv2.VideoCapture(0) 

# Technological classes: 0:person, 62:tv, 63:laptop, 67:cell phone
DEVICES = [0, 62, 63, 67]

def read_radar():
    # Define the exact absolute path where the server writes the data
    file_path = "/home/your_user/radar_project/radar_data.txt"
    
    if os.path.exists(file_path):
        # USE THE file_path VARIABLE to open it
        with open(file_path, "r") as f:
            lines = f.readlines()
            if lines:
                # Returns the last 5 detections for the HUD
                return lines[-5:] 
    return []

print("[*] Starting Local Vision...")

cv2.namedWindow("AI Radar HUD", cv2.WINDOW_NORMAL) # <--- MANDATORY to be resizable
cv2.resizeWindow("AI Radar HUD", 1024, 768)        # Large initial size

while True:
    ret, frame = cap.read()
    if not ret:
        print("[!] Cannot access the camera. Try changing the index in VideoCapture.")
        break

    # Execute optimized AI
    results = model(frame, verbose=False, classes=DEVICES, imgsz=320)
    annotated_frame = results[0].plot()

    # --- FLOATING TACTICAL HUD ---
    macs = read_radar()
    
    # If there is no real data, we draw nothing (clears the screen)
    if macs and "Waiting" not in macs[0]:
        y0, dy = 30, 25
        # Draw a small status text
        cv2.putText(annotated_frame, "RADAR LINK ACTIVE", (10, 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Draw the latest detections directly on the frame
        for i, line in enumerate(macs[-5:]): # Only the last 5
            text = line.strip()
            y = y0 + i * dy
            # Shadow effect so it can be read on any background
            cv2.putText(annotated_frame, text, (11, y+1), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            # Main text
            cv2.putText(annotated_frame, text, (10, y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

    # Show result
    cv2.imshow("TACTICAL HUD - QUEST 3", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
