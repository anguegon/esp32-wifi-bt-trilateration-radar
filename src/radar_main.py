import subprocess, os, time, sys, select

# --- SILENCE LOGS ---
os.environ['OPENCV_VIDEOIO_PRIORITY_BACKEND'] = 'V4L2'
os.environ['OPENCV_LOG_LEVEL'] = 'OFF'
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv_radar", "bin", "python3")
SERVER_DATA = os.path.join(BASE_DIR, "radar_server.py")
RADAR_VISION = os.path.join(BASE_DIR, "radar_vision_local.py")
OBJ_FILE = os.path.join(BASE_DIR, "detected_targets.txt")
PAUSE_FILE = os.path.join(BASE_DIR, ".pause")

def configure_firewall_auto():
    print("\033[1;33m[*] Configuring Firewall...\033[0m")
    try:
        subprocess.run(["sudo", "ufw", "allow", "50000/tcp"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "ufw", "allow", "5353/udp"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("\033[1;32m[OK] Firewall configured.\033[0m")
    except: pass

def launch_service(name, command_list, new_window=False, geometry="110x32", bg_color="#000000", fg_color="#00FF00"):
    if new_window:
        color_init = f"echo -ne '\\033]11;{bg_color}\\007\\033]10;{fg_color}\\007'; clear; "
        full_command = f"{color_init} {' '.join(command_list)}; exec bash"
        cmd = ["gnome-terminal", f"--geometry={geometry}", "--title=" + name, "--", "bash", "-c", full_command]
        return subprocess.Popen(cmd)
    else:
        # Aquí pasamos las variables de entorno para silenciar la visión AI
        env = os.environ.copy()
        env["OPENCV_LOG_LEVEL"] = "OFF"
        return subprocess.Popen(command_list, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    processes = []
    paused = False
    with open(PAUSE_FILE, "w") as f: f.write("0")

    configure_firewall_auto()

    try:
        processes.append(launch_service("TRAFFIC_HUD", [VENV_PYTHON, SERVER_DATA], True, "100x25", "#000000", "#00FF00"))
        time.sleep(2)
        processes.append(launch_service("TARGET_STATUS", [f"watch -n 1 -t cat {OBJ_FILE}"], True, "100x15", "#000000", "#FF3333"))
        
        # Lanzamos la visión pero su salida está redirigida a DEVNULL (silencio absoluto)
        processes.append(launch_service("AI_VISION", [VENV_PYTHON, RADAR_VISION], False))

        print("\n" + "="*40)
        print("\033[1;37m COMMANDS:\033[0m")
        print("\033[1;32m [P] + Enter: PAUSE/RESUME Analysis\033[0m")
        print("\033[1;31m [Ctrl+C]:    SHUTDOWN System\033[0m")
        print("="*40)
        print("\033[1;34m[*] Waiting for external device / Camera connection...\033[0m")

        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline().strip().lower()
                if 'p' in line:
                    paused = not paused
                    with open(PAUSE_FILE, "w") as f: f.write("1" if paused else "0")
                    status = "\033[1;41;37m PAUSE \033[0m" if paused else "\033[1;42;37m ACTIVE \033[0m"
                    print(f"\r{status} - Press 'P' to toggle.   ", end="", flush=True)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n\033[1;33m[*] Closing system...\033[0m")
        for p in processes: p.terminate()
        os.system("pkill -f radar_server.py")
        os.system("pkill -f watch")
        sys.exit(0)
