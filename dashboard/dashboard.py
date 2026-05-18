import requests
from rich.console import Console
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
    last = datetime.fromisoformat(last_seen)
    return datetime.now() - last > timedelta(hours=OFFLINE_THRESHOLD)

def status_indicator(machine: dict) -> Text:
    if is_offline(machine["last_seen"]):
        return Text("Offline", style="bold red")
    if machine["cpu_percent"] > 80 or machine["ram_percent"] > 80:
        return Text("ALERT", style="bold yellow")
    return Text("OK", style="bold green")

def build_machine_table(machines: list) -> Table:
    table = Table(title="PROATI Monitor - Machines", border_style="blue")

    table.add_column("Hostname", style="cyan")
    table.add_column("IP", style="white")
    table.add_column("User", style="white")
    table.add_column("Status", justify="center")
    table.add_column("CPU", justify="right")
    table.add_column("RAM", justify="right")
    table.add_column("Disk", justify="right")
    table.add_column("Peripherals", style="white")

    for machine in machines:
        offline = is_offline(machine["last_seen"])
        peripherals = ", ".join(machine["peripherals"]) if machine["peripherals"] else "---"

        table.add_row(
            machine["hostname"],
            machine["ip"],
            machine["user"] if not offline else "---",
            status_indicator(machine),
            f"{machine['cpu_percent']}%" if not offline else "---",
            f"{machine['ram_percent']}%" if not offline else "---",
            f"{machine['disk_percent']}%" if not offline else "---",
            peripherals if not offline else "---",
        )

    return table

def build_events_panel(events: list) -> Panel:
    if not events:
        content = Text("No recent events.", style="dim")
    else:
        content = Text()
        for event in events[:10]:
            timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")
            if event["type"] == "peripheral_removed":
                style = "bold red"
            elif event ["type"] == "peripheral_added":
                style = "bold yellow"
            else:
                style = "bold orange3"
            content.append(f"[{timestamp}]({event['hostname']} - {event['description']}\n", style=style)
    return Panel(content, title="Recent events", border_style="red")

def build_layout(machines: list, events: list):
    updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"\n[dim]Last updated: {updated}[/dim]")
    console.print(build_machine_table(machines))
    console.print(build_events_panel(events))

def main():
    console.print("[bold blue]Monitor Dashboard starting...[/bold blue]\n")
    with Live(refresh_per_second=1, screen=True) as live:
        while True:
            machines = get_machines()
            events = get_events()

            from rich.console import Group
            live.update(Group(
                build_machine_table(machines),
                build_events_panel(events),
            ))
            time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()