from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, event
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///proati.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    hostname = Column(String, index=True)
    ip = Column(String)
    last_seen = Column(DateTime, default=datetime.now(timezone.utc))

    snapshots = relationship("Snapshot", back_populates="machine", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="machine", cascade="all, delete-orphan")

class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    user = Column(String)
    cpu_percent = Column(Float)
    ram_percent = Column(Float)
    disk_percent = Column(Float)
    peripherals = Column(JSON)

    machine = relationship("Machine", back_populates="snapshots")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    type = Column(String)
    description = Column(String)

    machine = relationship("Machine", back_populates="events")

def init_db():
    Base.metadata.create_all(bind=engine)