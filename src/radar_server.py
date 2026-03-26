import socket, select, os, math, time
from zeroconf import ServiceInfo, Zeroconf

# =========================================================================
# --- AUTO-PATH CONFIGURATION ---
# =========================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OBJ_FILE = os.path.join(BASE_DIR, "detected_targets.txt")
PAUSE_FILE = os.path.join(BASE_DIR, ".pause")

# Diccionarios de estado global
detected_targets = {} 
device_database = {}
last_antenna_report = {"ALFA": 0, "BETA": 0, "GAMMA": 0}

# =========================================================================

PERSISTENCE_TIME = 300  # 5 minutes to remove
OFFLINE_TIME = 15       # 15 seconds to mark as Offline

# =========================================================================
# --- GEOGRAPHIC CONFIGURATION (MAPS) ---
# =========================================================================
# LAT_ORIGIN and LON_ORIGIN: Exact GPS coordinates of the ALFA antenna (0,0).
LAT_ORIGIN, LON_ORIGIN = 0, 0

# SYSTEM_AZIMUTH: Orientation of the imaginary line connecting ALFA with BETA.
# - If you walk from ALFA to BETA towards the EAST: Azimuth = 0
# - If you walk towards the NORTH: Azimuth = 90
# - If you walk towards the WEST: Azimuth = 180
# - If you walk towards the SOUTH: Azimuth = 270
SYSTEM_AZIMUTH = 180 

# =========================================================================
# --- PRECISION AND ENVIRONMENT SETTINGS ---
# =========================================================================
# ANTENNA_POSITIONS: Relative location in METERS of your nodes.
# All the antennas need to be inside of the range of a 2.4GHz network
# ALFA must always be (0.0, 0.0). BETA and GAMMA according to your physical measurements in meters. 
ANTENNA_POSITIONS = {"ALFA": (0.0, 0.0), "BETA": (0.0, 0.0), "GAMMA": (0.0, 0.0)}

# RSSI_1M: Power (dBm) received by the antenna when the phone is at 1 meter.
# - If the radar shows shorter distances than real: Lower this value (e.g., -45)
# - If it shows longer distances than real: Increase this value (e.g., -40)
RSSI_1M = -42

# N_PROP: Propagation factor (Signal loss due to obstacles).
# - OPEN SPACE (Field/Patio): Use 2.0
# - INDOOR WITH FURNITURE: Use 2.7 to 3.2
# - INDOOR WITH THICK WALLS: Use 3.5 to 4.0
N_PROP = 3.2 

# =========================================================================
# --- MATH ENGINE ---
# =========================================================================

def meters_to_gps(x, y):
    lat = LAT_ORIGIN + (y / 111320.0)
    lon = LON_ORIGIN + (x / (111320.0 * math.cos(math.radians(LAT_ORIGIN))))
    return round(lat, 7), round(lon, 7)

def get_cardinal_point(x, y):
    angle_rad = math.atan2(y, x)
    deg = (math.degrees(angle_rad) + SYSTEM_AZIMUTH) % 360
    sectors = [(22.5, 67.5, "NE"), (67.5, 112.5, "NORTH"), (112.5, 157.5, "NW"),
               (157.5, 202.5, "WEST"), (202.5, 247.5, "SW"), (247.5, 292.5, "SOUTH"),
               (292.5, 337.5, "SE"), (337.5, 360, "EAST"), (0, 22.5, "EAST")]
    for s, e, l in sectors:
        if s <= deg < e: return l
    return "EAST"

def trilateration(p1, p2, p3, r1, r2, r3):
    try:
        x1, y1 = p1; x2, y2 = p2; x3, y3 = p3
        A = 2*x2 - 2*x1
        B = 2*y2 - 2*y1
        C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
        D = 2*x3 - 2*x2
        E = 2*y3 - 2*y2
        F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2
        
        x = (C*E - F*B) / (A*E - D*B)
        y = (A*F - D*C) / (A*E - D*B)
        return x, y
    except ZeroDivisionError:
        return None
    except Exception as e:
        return None

# --- mDNS SETUP ---
s_ip = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s_ip.connect(("8.8.8.8", 80))
    local_ip = s_ip.getsockname()[0]
except:
    local_ip = "127.0.0.1"
finally:
    s_ip.close()

info_inst = ServiceInfo("_http._tcp.local.", "RadarServer._http._tcp.local.",
                        addresses=[socket.inet_aton(local_ip)], port=50000, server="radar.local.")
zc_inst = Zeroconf()
zc_inst.register_service(info_inst)
print(f"\033[1;36m[mDNS] Broadcast radar.local started on IP: {local_ip}\033[0m")
# ------------------

s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s_socket.bind(('0.0.0.0', 50000))
s_socket.listen(10)
s_socket.setblocking(False)

inputs = [s_socket]
connected_antennas = {} 

def update_target_file():
    now = time.time()
    to_remove = []
    
    with open(OBJ_FILE, "w") as f:
        f.write("=== TARGETS DETECTADOS ===\n")
        f.write("-" * 50 + "\n")
        for mac, info in detected_targets.items():
            if now - info['last_seen'] > 300: 
                to_remove.append(mac)
                continue
                
            status = "ONLINE" if now - info['last_seen'] < 15 else "OFFLINE"
            f.write(f"[{status}] {info['nombre']} | {mac}\n")
            f.write(f" -> Distancia Alfa: {info['dist_alfa']}m | Heading: {info['cardinal']}\n")
            f.write(f" -> Maps: https://www.google.com/maps?q={info['lat']},{info['lon']}\n")
            f.write("-" * 50 + "\n")
            
    for mac in to_remove:
        del detected_targets[mac]

print(f"\n[*] Radar Server Active on Port 50000. Listening...")

try:
    while True:
        try:
            with open(PAUSE_FILE, "r") as f:
                if f.read().strip() == "1":
                    time.sleep(1)
                    continue
        except: pass

        r, w, e = select.select(inputs, [], [], 0.5)

        for sock in r:
            if sock is s_socket:
                client_socket, client_address = s_socket.accept()
                inputs.append(client_socket)
            else:
                try:
                    data = sock.recv(4096).decode('utf-8', errors='ignore')
                    if data:
                        lines = data.split('\n')
                        if len(lines) > 0 and "ID:" in lines[0]:
                            connected_antennas[sock] = lines[0].split(":")[1].strip()
                        
                        s_id = connected_antennas.get(sock, "UNKNOWN")
                        if s_id == "UNKNOWN": continue

                        for line in lines:
                            if "|" not in line or "ID:" in line or "TYPE:" in line: continue
                            
                            parts = line.split("|")
                            if len(parts) >= 3:
                                name = parts[0].strip()
                                mac = parts[1].strip()
                                rssi_str = parts[2].replace("dBm", "").strip()
                                
                                try:
                                    rssi = int(rssi_str)
                                    dist = round(10 ** ((RSSI_1M - rssi) / (10 * N_PROP)), 2)
                                except ValueError:
                                    continue
                                
                                print(f"[{s_id}] {name} ({mac}) -> {dist}m")
                                
                                if mac not in device_database:
                                    device_database[mac] = {}
                                device_database[mac][s_id] = dist
                                
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
                                    device_database[mac] = {} 
                    else:
                        inputs.remove(sock)
                        if sock in connected_antennas: del connected_antennas[sock]
                        sock.close()
                except: 
                    if sock in inputs: inputs.remove(sock)
                    pass

except KeyboardInterrupt:
    print("\n[*] Shutting down server...")
    zc_inst.unregister_service(info_inst)
    zc_inst.close()
