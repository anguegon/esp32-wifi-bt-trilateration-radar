import socket, select, os, math, time

# =========================================================================
# --- GEOGRAPHIC CONFIGURATION (MAPS) ---
# =========================================================================
# LAT_ORIGIN and LON_ORIGIN: Exact GPS coordinates of the ALFA antenna (0,0).
LAT_ORIGIN, LON_ORIGIN = 0.0, 0.0 

# SYSTEM_AZIMUTH: Orientation of the imaginary line connecting ALFA with BETA.
# - If you walk from ALFA to BETA towards the EAST: Azimuth = 0
# - If you walk towards the NORTH: Azimuth = 90
# - If you walk towards the WEST: Azimuth = 180
# - If you walk towards the SOUTH: Azimuth = 270
SYSTEM_AZIMUTH = 180 

SERVER_IP = "192.168.1.100" # Your detected IP, run hostname -I in the terminal when changing locations

BASE_DIR = "/home/your_user/.../radar_project" #Replace by the route where you are using the code
OBJ_FILE = os.path.join(BASE_DIR, "detected_targets.txt")
PAUSE_FILE = os.path.join(BASE_DIR, ".pause")

# =========================================================================
# --- PRECISION AND ENVIRONMENT SETTINGS ---
# =========================================================================
# ANTENNA_POSITIONS: Relative location in METERS of your nodes.
# All the antennas need to be inside of the range of a 2.4GHz network
# ALFA must always be (0.0, 0.0). BETA and GAMMA according to your physical measurements in meters. 
ANTENNA_POSITIONS = {"ALFA": (0.0, 0.0), "BETA": (4.30, 0.0), "GAMMA": (2.70, 2.20)}

# RSSI_1M: Power (dBm) received by the antenna when the phone is at 1 meter.
# - If the radar shows shorter distances than real: Lower this value (e.g., -45)
# - If it shows longer distances than real: Increase this value (e.g., -40)
RSSI_1M = -42

# N_PROP: Propagation factor (Signal loss due to obstacles).
# - OPEN SPACE (Field/Patio): Use 2.0
# - INDOOR WITH FURNITURE: Use 2.7 to 3.2
# - INDOOR WITH THICK WALLS: Use 3.5 to 4.0
N_PROP = 3.2 

# MAX_REAL_RANGE: Discard filter to avoid distant "false positives".
# Since the home router saturates, if the calculation gives > 60m, the system ignores it.
MAX_REAL_RANGE = 60.0 

# =========================================================================

PERSISTENCE_TIME = 300  # 5 minutes to remove
OFFLINE_TIME = 15       # 15 seconds to mark as Offline

# --- MEMORY AND STATES ---
detected_targets = {} 
device_database = {}
# Dictionary to control the status of the antennas
last_antenna_report = {"ALFA": 0, "BETA": 0, "GAMMA": 0}

def show_network_hud():
    """Prints a network status table of the antennas in the terminal"""
    now = time.time()
    print("\n" + "="*45)
    print(f"        RADAR NETWORK STATUS | {time.strftime('%H:%M:%S')}")
    print("="*45)
    for ant in ["ALFA", "BETA", "GAMMA"]:
        diff = now - last_antenna_report[ant]
        if last_antenna_report[ant] == 0:
            status = "\033[91m[ NEVER SEEN ]\033[0m"
        elif diff < 10:
            status = "\033[92m[    ONLINE    ]\033[0m"
        else:
            status = f"\033[91m[ OFFLINE {int(diff)}s ]\033[0m"
        print(f" ANTENNA {ant:<5}: {status}")
    print("="*45 + "\n")

def get_cardinal_point(x, y):
    if x == 0 and y == 0: return "ORIGIN"
    angle_rad = math.atan2(y, x)
    relative_degrees = math.degrees(angle_rad)
    real_degrees = (relative_degrees + SYSTEM_AZIMUTH) % 360
    
    sectors = [
        (22.5, 67.5, "NE"), (67.5, 112.5, "NORTH"), (112.5, 157.5, "NW"),
        (157.5, 202.5, "WEST"), (202.5, 247.5, "SW"), (247.5, 292.5, "SOUTH"),
        (292.5, 337.5, "SE"), (337.5, 360, "EAST"), (0, 22.5, "EAST")
    ]
    for start, end, label in sectors:
        if start <= real_degrees < end: return label
    return "EAST"

def meters_to_gps(x_met, y_met):
    R = 6378137 
    angle_rad = math.radians(SYSTEM_AZIMUTH)
    x_rot = x_met * math.cos(angle_rad) - y_met * math.sin(angle_rad)
    y_rot = x_met * math.sin(angle_rad) + y_met * math.cos(angle_rad)
    dLat = y_rot / R
    dLon = x_rot / (R * math.cos(math.pi * LAT_ORIGIN / 180))
    return round(LAT_ORIGIN + (dLat * 180 / math.pi), 7), round(LON_ORIGIN + (dLon * 180 / math.pi), 7)

def trilateration(p1, p2, p3, r1, r2, r3):
    if any(r > MAX_REAL_RANGE for r in [r1, r2, r3]): return None
    try:
        x1, y1 = p1; x2, y2 = p2; x3, y3 = p3
        A, B = 2*x2 - 2*x1, 2*y2 - 2*y1
        C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
        D, E = 2*x3 - 2*x2, 2*y3 - 2*y2
        F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2
        x = (C*E - F*B) / (A*E - D*B)
        y = (A*F - D*C) / (A*E - D*B)
        return x, y
    except: return None

def update_target_file():
    with open(OBJ_FILE, 'w') as f:
        f.write(f"=== RADAR | {time.strftime('%H:%M:%S')} | MODE: MOBILE ===\n")
        f.write(f"{'DEVICE':<15} | {'STATUS':<8} | {'SEEN':<6} | {'COORDINATES'}\n")
        f.write("-" * 100 + "\n")
        for mac, info in detected_targets.items():
            seen = int(time.time() - info['last_seen'])
            visual_status = "[ON]" if info['status'] == "ONLINE" else "[OFF]"
            
            # Corrected URL format for Google Maps
            url_maps = f"https://www.google.com/maps?q={info['lat']},{info['lon']}"
            
            f.write(f"{info['nombre'][:15]:<15} | {visual_status:<8} | {seen:>3}s | {info['lat']},{info['lon']}\n")
            f.write(f"   HEADING: {info['cardinal']:<6} | DIST: {info['dist_alfa']}m\n")
            f.write(f"   LINK: {url_maps}\n")
            f.write("-" * 100 + "\n")

# --- SERVER START ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 50000))
s.listen(10)
s.setblocking(False) 
inputs = [s]
connected_antennas = {}

print(f"\033[1;32m[*] RADAR SERVER ACTIVE ON {SERVER_IP}:50000\033[0m")

last_hud_update = 0

while True:
    # Update network HUD every 2 seconds
    if time.time() - last_hud_update > 2:
        show_network_hud()
        last_hud_update = time.time()

    # Pause check
    paused = False
    if os.path.exists(PAUSE_FILE):
        try:
            with open(PAUSE_FILE, "r") as pf: paused = (pf.read().strip() == "1")
        except: pass

    r, _, _ = select.select(inputs, [], [], 0.5)
    for sock in r:
        if sock is s:
            conn, addr = s.accept()
            inputs.append(conn)
        else:
            try:
                data = sock.recv(4096).decode('utf-8', errors='ignore')
                if data:
                    if paused: continue
                    
                    # Identification and marking of antenna activity
                    s_id = "UNKNOWN"
                    if "ID:GAMMA" in data.upper(): s_id = "GAMMA"
                    elif "ID:BETA" in data.upper(): s_id = "BETA"
                    elif "ID:ALFA" in data.upper(): s_id = "ALFA"
                    
                    if s_id != "UNKNOWN":
                        connected_antennas[sock] = s_id
                        last_antenna_report[s_id] = time.time()

                    current_s_id = connected_antennas.get(sock, "ALFA")
                    color = "\033[92m" if current_s_id == "ALFA" else "\033[93m" if current_s_id == "BETA" else "\033[96m"
                    
                    for line in data.split('\n'):
                        if "|" not in line or "ID:" in line: continue
                        parts = line.split("|")
                        if len(parts) < 3: continue
                        
                        name = parts[0].strip() or "Anon"
                        mac = parts[1].strip().upper()
                        try:
                            rssi = int(parts[2].replace("dBm", "").strip())
                            dist = round(10 ** ((RSSI_1M - rssi) / (10 * N_PROP)), 2)
                        except: continue

                        # Print traffic to terminal
                        print(f"{color}[{current_s_id}]\033[0m {name} | {mac[:17]} | {dist}m")

                        if mac not in device_database: device_database[mac] = {}
                        device_database[mac][current_s_id] = dist
                        
                        # Process only if we have data from all 3 antennas
                        if all(k in device_database[mac] for k in ["ALFA", "BETA", "GAMMA"]):
                            res = trilateration(ANTENNA_POSITIONS["ALFA"], ANTENNA_POSITIONS["BETA"], ANTENNA_POSITIONS["GAMMA"],
                                             device_database[mac]["ALFA"], device_database[mac]["BETA"], device_database[mac]["GAMMA"])
                            if res:
                                lat, lon = meters_to_gps(res[0], res[1])
                                total_dist = round(math.sqrt(res[0]**2 + res[1]**2), 2)
                                heading = get_cardinal_point(res[0], res[1])
                                
                                detected_targets[mac] = {
                                    "nombre": name, "lat": lat, "lon": lon, 
                                    "dist_alfa": total_dist, "cardinal": heading,
                                    "last_seen": time.time(), "status": "ONLINE"
                                }
                                update_target_file()
                                print(f"\033[1;91m[FIX] {name} -> {heading} ({total_dist}m)\033[0m")
                            device_database[mac] = {} # Clear memory for this target
                else:
                    inputs.remove(sock)
                    if sock in connected_antennas: del connected_antennas[sock]
                    sock.close()
            except: 
                if sock in inputs: inputs.remove(sock)
                pass
