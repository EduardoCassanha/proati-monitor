import psutil
import wmi
import requests
import socket
import getpass
from datetime import datetime
import time
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

SERVER_URL = config["server"]["url"]
INTERVAL = 60

psutil.cpu_percent(interval=None)


def get_machine_info() -> dict:
    c = wmi.WMI()
    hw_uuid = "UNKNOWN"
    try:
        for system in c.Win32_ComputerSystemProduct():
            hw_uuid = system.UUID
            break
    except Exception:
        pass

    return {
        "uuid": hw_uuid,
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "user": getpass.getuser(),
    }


def get_hardware_info() -> dict:
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
    }


def get_peripherals() -> list:
    c = wmi.WMI()
    devices = []

    wmi_query = "SELECT Name, DeviceID, Status FROM Win32_PnPEntity"

    try:
        for device in c.query(wmi_query):
            if device.DeviceID and device.Name:
                device_id_upper = device.DeviceID.upper()

                if device_id_upper.startswith("USB") or device_id_upper.startswith("HID"):
                    if "root" not in device_id_upper.lower():
                        devices.append({
                            "name": device.Name,
                            "type": "Hardware Device",
                            "status": device.Status if device.Status else "OK",
                        })
    except Exception:
        pass

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
        response = requests.post(f"{SERVER_URL}/snapshot", json=snapshot, timeout=10)
        response.raise_for_status()
        print(f"[{snapshot['timestamp']}]: Snapshot sent successfully.")
    except requests.RequestException as e:
        print(f"[{snapshot['timestamp']}] Failed to send snapshot: {e}")


def main():
    print("Agent Starting...")
    while True:
        snapshot = collect_snapshot()
        send_snapshot(snapshot)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()