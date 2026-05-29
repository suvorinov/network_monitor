from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Computer(Base):
    """Модель компьютера в сети для хранения метрик."""
    __tablename__ = "computers"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True)
    ip_address = Column(String, nullable=True)
    os_name = Column(String, default="Unknown")
    current_user = Column(String, default="Unknown") # <--- НОВОЕ ПОЛЕ
    status = Column(String, default="OFFLINE")
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    cpu_percent = Column(Float, default=0)
    ram_percent = Column(Float, default=0)
    ram_total_gb = Column(Float, default=0)
    ram_available_gb = Column(Float, default=0)
    
    disk_percent = Column(Float, default=0)
    disk_total_gb = Column(Float, default=0)
    disk_free_gb = Column(Float, default=0)
    
    uptime_seconds = Column(Integer, default=0)
    process_count = Column(Integer, default=0)
    
    bytes_sent_mb = Column(Float, default=0)
    bytes_recv_mb = Column(Float, default=0)
    
    swap_percent = Column(Float, default=0)
