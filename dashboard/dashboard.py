import requests
from rich.console import Console, Group
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from datetime import datetime, timedelta
import time

SERVER_URL = "http://localhost:8000"
REFRESH_INTERVAL = 30
OFFLINE_THRESHOLD = 10

console = Console()


def get_machines() -> list:
    try:
        response = requests.get(f"{SERVER_URL}/machines", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


def get_events() -> list:
    try:
        response = requests.get(f"{SERVER_URL}/events", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


def is_offline(last_seen: str) -> bool:
    try:
        last = datetime.fromisoformat(last_seen)
        return datetime.now() - last > timedelta(minutes=OFFLINE_THRESHOLD)
    except (ValueError, TypeError):
        return True


def status_indicator(machine: dict, offline: bool) -> Text:
    if offline:
        return Text("Offline", style="bold red")

    cpu = machine.get("cpu_percent", 0)
    ram = machine.get("ram_percent", 0)

    if cpu > 80 or ram > 80:
        return Text("ALERT", style="bold yellow")
    return Text("OK", style="bold green")


def build_machine_table(machines: list) -> Table:
    table = Table(title="PROATI Monitor - Machines", border_style="blue", show_lines=True)

    table.add_column("Hostname", style="cyan")
    table.add_column("IP", style="white")
    table.add_column("User", style="white")
    table.add_column("Status", justify="center")
    table.add_column("CPU", justify="right")
    table.add_column("RAM", justify="right")
    table.add_column("Disk", justify="right")
    table.add_column("Peripherals", style="white")

    for machine in machines:
        offline = is_offline(machine.get("last_seen", ""))

        raw_peripherals = machine.get("peripherals", [])

        filtered_peripherals = [
            p for p in raw_peripherals
            if "mouse" in p.lower() or "keyboard" in p.lower() or "teclado" in p.lower()
        ]

        peripherals = ", ".join(filtered_peripherals) if filtered_peripherals else "---"

        cpu_val = machine.get("cpu_percent")
        ram_val = machine.get("ram_percent")
        disk_val = machine.get("disk_percent")

        table.add_row(
            machine.get("hostname", "Unknown"),
            machine.get("ip", "---"),
            machine.get("user", "---") if not offline else "---",
            status_indicator(machine, offline),
            f"{cpu_val}%" if (not offline and cpu_val is not None) else "---",
            f"{ram_val}%" if (not offline and ram_val is not None) else "---",
            f"{disk_val}%" if (not offline and disk_val is not None) else "---",
            peripherals if not offline else "---",
        )

    return table


def build_events_panel(events: list) -> Panel:
    if not events:
        content = Text("No recent events.", style="dim")
    else:
        content = Text()
        for event in events[:10]:
            try:
                timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")
            except (ValueError, TypeError):
                timestamp = "??:??:??"

            if event.get("type") == "peripheral_removed":
                style = "bold red"
            elif event.get("type") == "peripheral_added":
                style = "bold green"
            else:
                style = "bold orange3"

            content.append(
                f"[{timestamp}] {event.get('hostname', 'Unknown')} - {event.get('description', 'No description')}\n",
                style=style
            )
    return Panel(content, title="Recent events", border_style="red")


def main():
    console.print("[bold blue]Monitor Dashboard starting...[/bold blue]\n")

    machines = []
    events = []
    last_update = 0

    with Live(refresh_per_second=1, screen=True) as live:
        while True:
            current_time = time.time()

            if current_time - last_update >= REFRESH_INTERVAL or last_update == 0:
                machines = get_machines()
                events = get_events()
                last_update = current_time

            live.update(Group(
                build_machine_table(machines),
                build_events_panel(events),
            ))

            time.sleep(1)


if __name__ == "__main__":
    main()