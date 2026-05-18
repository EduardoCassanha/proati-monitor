import psutil
import wmi
import requests
import socket
import getpass
from datetime import datetime
import time

SERVER_URL = "http://localhost:8000"
INTERVAL = 60

def get_machine_info() -> dict:
    return {
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "user": getpass.getuser(),
    }

def get_hardware_info() -> dict:
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
    }

def get_peripherals() -> dict:
    c = wmi.WMI()
    devices = []

    for device in c.Win32_PnPEntity():
        if device.PNPClass in ("Mouse", "Keyboard", "Monitor", "USB"):
            devices.append({
                "name": device.Name,
                "type": device.PNPClass,
                "status": device.Status,
            })

    return devices

def collect_snapshot() -> dict:
    return {
        "timestamp": datetime.now().isoformat(),
        **get_machine_info(),
        **get_hardware_info(),
        "peripherals": get_peripherals(),
    }

def send_snapshot(snapshot: dict):
    try:
        response = requests.post(f"{SERVER_URL}/snapshot/", json=snapshot, timeout=10)
        response.raise_for_status()
        print(f"[{snapshot['timestamp']}]: Snapshot sent successfully.")
    except requests.RequestException as e:
        print(f"[{snapshot['timestamp']}] Failed to send snapshot: {e}")

def main ():
    print("Agent Starting...")
    while True:
        snapshot = collect_snapshot()
        send_snapshot(snapshot)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()