"""SQLAlchemy database models."""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text
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
    raw_data = Column(JSON)  # Store full Garmin API response
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HeartRateData(Base):
    """Heart rate time series data model."""

    __tablename__ = "heart_rate_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(String, nullable=False)  # Foreign key to activities
    timestamp = Column(DateTime, nullable=False)
    heart_rate = Column(Integer, nullable=False)
    zone = Column(Integer)  # Heart rate zone (1-5)
    created_at = Column(DateTime, default=datetime.utcnow)


class ActivityInterval(Base):
    """Activity interval model for changepoint detection results."""

    __tablename__ = "activity_intervals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(String, nullable=False)  # Foreign key to activities
    interval_index = Column(Integer, nullable=False)  # Interval number within activity
    start_idx = Column(Integer, nullable=False)  # Start index in data array
    end_idx = Column(Integer, nullable=False)  # End index in data array
    start_time = Column(DateTime, nullable=True)  # Actual start timestamp
    end_time = Column(DateTime, nullable=True)  # Actual end timestamp
    duration_seconds = Column(Float, nullable=True)
    duration_samples = Column(Integer, nullable=False)

    # Heart rate stats
    hr_mean = Column(Float, nullable=True)
    hr_std = Column(Float, nullable=True)
    hr_min = Column(Integer, nullable=True)
    hr_max = Column(Integer, nullable=True)
    hr_median = Column(Float, nullable=True)

    # Cadence stats (if available)
    cadence_mean = Column(Float, nullable=True)
    cadence_std = Column(Float, nullable=True)
    cadence_min = Column(Float, nullable=True)
    cadence_max = Column(Float, nullable=True)

    # Power stats (if available)
    power_mean = Column(Float, nullable=True)
    power_std = Column(Float, nullable=True)
    power_min = Column(Float, nullable=True)
    power_max = Column(Float, nullable=True)

    # Detection parameters
    penalty = Column(Float, nullable=True)
    model = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkoutMetadata(Base):
    """User-provided metadata for workouts (RPE, session structure, notes)."""

    __tablename__ = "workout_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(String, nullable=False, unique=True)  # Foreign key to activities

    # Subjective metrics
    rpe = Column(Integer, nullable=True)  # Rate of Perceived Exertion (1-10)
    feeling = Column(String, nullable=True)  # How the workout felt (great, good, okay, bad, terrible)
    mood = Column(String, nullable=True)  # Pre-workout mood

    # Session structure
    session_structure = Column(JSON, nullable=True)  # Structured session description (e.g., warmup, intervals, cooldown)
    focus_areas = Column(JSON, nullable=True)  # List of focus areas (e.g., ["endurance", "speed", "technique"])

    # Notes
    notes = Column(Text, nullable=True)  # Free-form notes about the workout
    lessons_learned = Column(Text, nullable=True)  # Key takeaways

    # Planning context
    planned_workout = Column(String, nullable=True)  # What was planned vs actual
    deviations = Column(Text, nullable=True)  # Any deviations from plan

    # Recovery
    recovery_notes = Column(Text, nullable=True)  # Post-workout recovery notes
    sleep_quality = Column(Integer, nullable=True)  # Sleep quality night before (1-10)
    stress_level = Column(Integer, nullable=True)  # Stress level before workout (1-10)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
