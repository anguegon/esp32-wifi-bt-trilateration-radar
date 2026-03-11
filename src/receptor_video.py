import cv2
import numpy as np
import socket
from ultralytics import YOLO

# You only use this code if wou want to execute the code in a RPi instead of a PC, to make the proyect even more portable.
# Nowadays I'm not really using it because my RPi doesn't have enough RAM to run the AI and the rest of the code.

# 1. Load the AI brain
model = YOLO('yolov8n.pt')

# 2. Configure TCP tunnel
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind(('0.0.0.0', 50001))
server_sock.listen(1)

print("[*] AI HUD waiting for RPi connection...")
conn, addr = server_sock.accept()
print(f"[+] Radar connected to RPi at {addr}")

# Buffer to reconstruct images
data_buffer = b""

try:
    while True:
        # Receive data chunks
        chunk = conn.recv(1024 * 16)
        if not chunk: break
        data_buffer += chunk

        # Look for the start (0xffd8) and end (0xffd9) of a JPEG image
        a = data_buffer.find(b'\xff\xd8')
        b = data_buffer.find(b'\xff\xd9')

        if a != -1 and b != -1:
            jpg_data = data_buffer[a:b+2]
            data_buffer = data_buffer[b+2:] # Clear buffer for the next one

            # Decode image
            frame = cv2.imdecode(np.frombuffer(jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)

            # --- CLASS CONFIGURATION ---
            # 0: person, 62: tv, 63: laptop, 65: remote, 66: keyboard, 67: cell phone
            NETWORK_DEVICES = [0, 62, 63, 65, 66, 67]

            if frame is not None:
                # Filtered AI: Only search for humans and technology
                results = model(frame, 
                                verbose=False, 
                                classes=NETWORK_DEVICES, 
                                imgsz=320, 
                                conf=0.4) # Lowering confidence to 0.4 to catch small gadgets
            
                # Plot results
                annotated_frame = results[0].plot()

                # --- INSERT YOUR MAC FUSION LOGIC HERE ---
                # (Code to read radar_data.txt and draw it on screen)

                # Show window (This is what you will see in the Quest 3)
                cv2.imshow("RADAR HUD - AI ACTIVE", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    conn.close()
    server_sock.close()
    cv2.destroyAllWindows()
