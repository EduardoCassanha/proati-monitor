# PROATI Monitor

Infrastructure monitoring system for public school computer labs.
Tracks hardware usage and peripheral devices in real time.

## Components

- **Agent** - runs silently on each PC, collects data every minute
- **Server** - receives and stores data, detects events
- **Dashboard** - real-time console monitor

## Stack

- Python + psutil + wmi (agent)
- Python + FastAPI + SQLAlchemy + SQLit (server)
- Python + rich (dashboard)

## Getting Started

### Server
Run `server/server.exe` on the dedicated PC.

### Agent
1. Edit `agent/config.ini` with the server IP
2. Run `agent/install.bat` as administrator on each PC

### Dashboard
Run `dashboard/dashboard.exe` to start monitoring.

## Alerts

Alert: CPU or RAM above 80%
Offline: PC not responding for 10+ minutes

Peripheral removed: Device disconnected since last snapshot

Peripheral added: New device connected