import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models.audit import Base

# Resolve path relative to this file (backend/app/database.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Use sqlite:/// prefix for absolute path compatibility with SQLAlchemy
SQLALCHEMY_DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "audit.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Initialize audit database tables."""
    Base.metadata.create_all(bind=engine)