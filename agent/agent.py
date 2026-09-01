import psutil
import wmi
import requests
import socket
from datetime import datetime
import time
import sys
import os
import configparser

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

INTERVAL = 60
DISCOVERY_PORT = 8001
DISCOVERY_TIMEOUT = 3.0

config = configparser.ConfigParser()
config_file = "config.ini"


def get_configured_url() -> str:
    if os.path.exists(config_file):
        config.read(config_file)
        if "server" in config and "url" in config["server"]:
            return config["server"]["url"].rstrip("/")
    return ""


def save_configured_url(url: str):
    config["server"] = {"url": url}
    try:
        with open(config_file, "w") as f:
            config.write(f)
    except Exception:
        pass


def discover_server_url() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(DISCOVERY_TIMEOUT)

    server_found_url = None
    try:
        sock.sendto(b"PROATI_DISCOVER", ("255.255.255.255", DISCOVERY_PORT))
        data, addr = sock.recvfrom(1024)
        msg = data.decode("utf-8")

        if msg.startswith("PROATI_SERVER_HERE:"):
            port = msg.split(":")[1]
            server_ip = addr[0]
            server_found_url = f"http://{server_ip}:{port}"
            print(f"[Discovery] Server found in: {server_found_url}")
    except socket.timeout:
        pass
    except Exception as e:
        print(f"[Discovery Error] {e}")
    finally:
        sock.close()

    return server_found_url


psutil.cpu_percent(interval=None)
WMI_CLIENT = wmi.WMI()


def get_logged_in_user() -> str:
    try:
        computer_system = WMI_CLIENT.Win32_ComputerSystem()[0]
        username_completo = computer_system.UserName
        if username_completo:
            return username_completo.split("\\")[-1]
        return "No user logged"
    except Exception:
        return "UNKNOWN_USER"


def get_static_machine_info() -> dict:
    hw_uuid = "UNKNOWN"
    try:
        for system in WMI_CLIENT.Win32_ComputerSystemProduct():
            hw_uuid = system.UUID
            break
    except Exception:
        pass
    return {"uuid": hw_uuid}


def get_dynamic_machine_info() -> dict:
    try:
        hostname = socket.gethostname()
        ip_addr = socket.gethostbyname(hostname)
    except Exception:
        hostname = "UNKNOWN"
        ip_addr = "127.0.0.1"

    return {
        "hostname": hostname,
        "ip": ip_addr,
        "user": get_logged_in_user(),
    }


def get_hardware_info() -> dict:
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
    }


def get_peripherals() -> list:
    devices = []
    wmi_query = "SELECT Name, DeviceID, Status FROM Win32_PnPEntity"

    try:
        for device in WMI_CLIENT.query(wmi_query):
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


def collect_snapshot(static_info: dict) -> dict:
    return {
        "timestamp": datetime.now().isoformat(),
        **static_info,
        **get_dynamic_machine_info(),
        **get_hardware_info(),
        "peripherals": get_peripherals(),
    }


def send_snapshot(snapshot: dict, target_url: str) -> bool:
    try:
        response = requests.post(f"{target_url}/snapshot", json=snapshot, timeout=5)
        response.raise_for_status()
        print(f"[{snapshot['timestamp']}]: Snapshot sent successfully to {target_url}.")
        return True
    except requests.RequestException as e:
        print(f"[{snapshot['timestamp']}] Failed to send snapshot: {e}")
        return False


def main():
    print("Agent Starting...")
    static_info = get_static_machine_info()
    current_url = get_configured_url()

    while True:
        if not current_url:
            print("Trying server auto-discover...")
            discovered = discover_server_url()
            if discovered:
                current_url = discovered
                save_configured_url(current_url)

        snapshot = collect_snapshot(static_info)

        success = False
        if current_url:
            success = send_snapshot(snapshot, current_url)

        if not success:
            print("Communication failure. Starting new research...")
            current_url = None
            time.sleep(5)
            continue

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()