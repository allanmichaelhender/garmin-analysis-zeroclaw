"""SQLAlchemy database models."""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Activity(Base):
    """Garmin activity model."""

    __tablename__ = "activities"

    id = Column(String, primary_key=True)  # Garmin activity ID
    activity_type = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer)
    distance_meters = Column(Float)
    avg_heart_rate = Column(Integer)
    max_heart_rate = Column(Integer)
    calories = Column(Integer)
    avg_speed = Column(Float)
    max_speed = Column(Float)
    elevation_gain = Column(Float)
    elevation_loss = Column(Float)
    avg_cadence = Column(Float)
    max_cadence = Column(Float)
    avg_power = Column(Float)
    max_power = Column(Float)
    training_effect = Column(Float)
    aerobic_effect = Column(Float)
    anaerobic_effect = Column(Float)
    raw_data = Column(JSON)  # Store full Garmin API response (activity list)
    metrics_data = Column(
        JSON, nullable=True
    )  # Store 1-second metrics (HR, timestamps, cadence, etc.)
    splits_data = Column(
        JSON, nullable=True
    )  # Store activity splits/intervals from Garmin API
    is_intervals = Column(
        String, nullable=True
    )  # "true" or "false" — whether workout is interval-based
    workout_structure = Column(
        String, nullable=True
    )  # Description of workout structure
    anthropic_hr_profile = Column(
        String, nullable=True
    )  # Anthropic-generated HR profile summary
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
