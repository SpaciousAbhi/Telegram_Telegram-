import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    source_id = Column(String, nullable=False) # Channel ID or Username
    source_title = Column(String) # Readable Name
    target_id = Column(String, nullable=False) # Channel ID or Username
    target_title = Column(String) # Readable Name

    # Configuration
    mode = Column(String, default='live') # 'live' or 'history'
    is_active = Column(Boolean, default=True)
    config = Column(JSON, default=dict) # Filters, Specific Rules

    # State
    last_processed_id = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    error_count = Column(Integer, default=0)

class GlobalSettings(Base):
    __tablename__ = 'settings'

    key = Column(String, primary_key=True)
    value = Column(JSON) # Storing complex rules as JSON

class AppLog(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String) # INFO, ERROR, WARNING
    message = Column(Text)
    task_id = Column(Integer, nullable=True)

# Database Setup
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

DB_URI = DATABASE_URL if DATABASE_URL else 'sqlite:///userbot.db'

engine = create_engine(DB_URI, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
