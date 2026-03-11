import subprocess, os, time, sys, select

# --- PATH CONFIGURATION ---
BASE_DIR = "/home/your_user/.../radar_project"
VENV_PYTHON = "/home/your_user/.../radar_project/venv_radar/bin/python3"
SERVER_DATA = os.path.join(BASE_DIR, "radar_server.py")
RADAR_VISION = os.path.join(BASE_DIR, "radar_vision_local.py")
OBJ_FILE = os.path.join(BASE_DIR, "detected_targets.txt")
PAUSE_FILE = os.path.join(BASE_DIR, ".pause")

def configure_firewall_auto():
    """Automatically opens port 50000 in the Ubuntu firewall."""
    print("\033[1;33m[*] Configuring Firewall (Port 50000)...\033[0m")
    try:
        # Executes sudo command so that if you already have permissions it won't ask for a password, 
        # or it will only ask once at the beginning of the script.
        subprocess.run(["sudo", "ufw", "allow", "50000/tcp"], check=True, stdout=subprocess.DEVNULL)
        print("\033[1;32m[OK] Firewall configured successfully.\033[0m")
    except Exception as e:
        print(f"\033[1;31m[!] Firewall configuration error: {e}\033[0m")

def launch_service(name, command_list, new_window=False, geometry="110x32", color="green"):
    print(f"[*] Launching: {name}...")
    if new_window:
        cmd_str = " ".join(command_list)
        # -sb enables scrollbar, -T sets the title
        full_cmd = f"xterm -sb -sl 2000 -T '{name}' -bg black -fg {color} -geometry {geometry} -e 'bash -c \"{cmd_str}; exec bash\"'"
        return subprocess.Popen(full_cmd, shell=True)
    else:
        return subprocess.Popen(command_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    # 0. Pre-system configuration
    configure_firewall_auto()

    # 1. Initial cleanup of exchange files
    for f_path in [PAUSE_FILE, OBJ_FILE]:
        if os.path.exists(f_path): os.remove(f_path)
        
    with open(PAUSE_FILE, "w") as f: f.write("0")
    with open(OBJ_FILE, "w") as f: f.write("WAITING FOR ANTENNA SIGNAL...")

    processes = []
    paused = False 

    try:
        print("\033[1;34m" + "="*40)
        print("    RADAR MASTER: ACCESS POINT MODE")
        print("="*40 + "\033[0m")
        print("[i] Press 'P' to Pause/Resume")
        print("[i] Press 'Ctrl+C' to Exit")

        # 2. LAUNCH SERVICES
        
        # Traffic Server (Now includes the antenna connection HUD)
        # Launched with sudo to ensure full network permissions
        processes.append(launch_service("TRAFFIC_AND_HUD", ["sudo", VENV_PYTHON, SERVER_DATA], True, "100x25", "green"))
        
        time.sleep(2) # Wait for the socket to open

        # Object Monitor (Real-time text file watch)
        processes.append(launch_service("TARGET_STATUS", [f"watch -n 1 -t cat {OBJ_FILE}"], True, "100x15", "red"))

        # AI Vision (HUD over camera)
        processes.append(launch_service("AI_VISION", [VENV_PYTHON, RADAR_VISION], False))

        while True:
            # Non-blocking keyboard input for remote system control
            if select.select([sys.stdin], [], [], 0.1)[0]:
                key = sys.stdin.readline().strip().lower()
                
                if key == 'p':
                    paused = not paused
                    with open(PAUSE_FILE, "w") as f:
                        f.write("1" if paused else "0")
                        
                    if paused:
                        print("\033[1;41;37m MODE: PAUSE \033[0m - Server on standby.")
                    else:
                        print("\033[1;42;37m MODE: ACTIVE \033[0m - Processing trilateration.")

            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\033[1;33m[*] Closing radar system and releasing ports...\033[0m")
        for p in processes:
            p.terminate()
        
        # Temporary file cleanup
        if os.path.exists(PAUSE_FILE): os.remove(PAUSE_FILE)
        print("[OK] System closed.")
        sys.exit(0)
