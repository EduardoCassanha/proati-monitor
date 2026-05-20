import sys
import os

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, init_db, Machine, Snapshot, Event
from datetime import datetime
from pydantic import BaseModel
from contextlib import asynccontextmanager

class PeripheralSchema(BaseModel):
    name: str
    type: str
    status: str

class SnapshotSchema(BaseModel):
    uuid: str
    hostname: str
    ip: str
    user: str
    timestamp: str
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    peripherals: list[PeripheralSchema]

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title="PROATI Monitor", lifespan=lifespan)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def detect_events(db: Session, machine: Machine, snapshot: Snapshot, current_peripherals: list):
    last_snapshot = (
        db.query(Snapshot)
        .filter(Snapshot.machine_id == machine.id)
        .order_by(Snapshot.id.desc())
        .offset(1)
        .first()
    )

    if last_snapshot:
        previous = {p["name"] for p in last_snapshot.peripherals}
        current = {p["name"] for p in current_peripherals}

        for missing in previous - current:
            event = Event(
                machine_id=machine.id,
                type="peripheral_removed",
                description=f"Peripheral removed {missing}",
            )
            db.add(event)

        for added in current - previous:
            event = Event(
                machine_id=machine.id,
                type="peripheral_added",
                description=f"Peripheral added {added}",
            )
            db.add(event)

    if snapshot.cpu_percent > 80:
        db.add(Event(
            machine_id=machine.id,
            type="high_cpu",
            description=f"High CPU usage: {snapshot.cpu_percent}%",
        ))

    if snapshot.ram_percent > 80:
        db.add(Event(
            machine_id=machine.id,
            type="high_ram",
            description=f"High RAM usage: {snapshot.ram_percent}%",
        ))

@app.post("/snapshot")
def receive_snapshot(data: SnapshotSchema, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.uuid == data.uuid).first()

    if not machine:
        machine = Machine(uuid=data.uuid, hostname=data.hostname, ip=data.ip)
        db.add(machine)
        db.flush()

    machine.hostname = data.hostname
    machine.ip = data.ip
    machine.last_seen = datetime.now()

    peripherals = [p.model_dump() for p in data.peripherals]

    snapshot = Snapshot(
        machine_id=machine.id,
        timestamp=datetime.fromisoformat(data.timestamp),
        user=data.user,
        cpu_percent=data.cpu_percent,
        ram_percent=data.ram_percent,
        disk_percent=data.disk_percent,
        peripherals=peripherals,
    )
    db.add(snapshot)
    db.flush()

    detect_events(db, machine, snapshot, peripherals)
    db.commit()

    return {"status": "ok"}

@app.get("/machines")
def get_machines(db: Session = Depends(get_db)):
    machines = db.query(Machine).all()
    result = []

    for machine in machines:
        last_snapshot = (
            db.query(Snapshot)
            .filter(Snapshot.machine_id == machine.id)
            .order_by(Snapshot.id.desc())
            .first()
        )

        peripherals = []
        if last_snapshot and last_snapshot.peripherals:
            peripherals = [p["name"] for p in last_snapshot.peripherals if "name" in p]

        result.append({
            "hostname": machine.hostname,
            "ip": machine.ip,
            "last_seen": machine.last_seen.isoformat(),
            "user": last_snapshot.user if last_snapshot else None,
            "cpu_percent": last_snapshot.cpu_percent if last_snapshot else 0,
            "ram_percent": last_snapshot.ram_percent if last_snapshot else 0,
            "disk_percent": last_snapshot.disk_percent if last_snapshot else 0,
            "peripherals": peripherals,
        })

    return result

@app.get("/events")
def get_events(db: Session = Depends(get_db)):
    events = (
        db.query(Event, Machine)
        .join(Machine, Event.machine_id == Machine.id)
        .order_by(Event.timestamp.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "hostname": machine.hostname,
            "timestamp": event.timestamp.isoformat(),
            "type": event.type,
            "description": event.description,
        }
        for event, machine in events
    ]

import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)