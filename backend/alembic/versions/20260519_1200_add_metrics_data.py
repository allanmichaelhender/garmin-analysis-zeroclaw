"""Add metrics_data to activities, drop unused tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-19 12:00:00

"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add metrics_data JSON column to activities table
    op.add_column("activities", sa.Column("metrics_data", sa.JSON(), nullable=True))

    # Drop unused tables (consolidated into activities)
    op.drop_table("workout_metadata")
    op.drop_table("activity_intervals")
    op.drop_table("heart_rate_data")


def downgrade() -> None:
    # Re-create heart_rate_data table
    op.create_table(
        "heart_rate_data",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("activity_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("heart_rate", sa.Integer(), nullable=False),
        sa.Column("zone", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
    )

    # Re-create activity_intervals table
    op.create_table(
        "activity_intervals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("activity_id", sa.String(), nullable=False),
        sa.Column("interval_index", sa.Integer(), nullable=False),
        sa.Column("start_idx", sa.Integer(), nullable=False),
        sa.Column("end_idx", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime()),
        sa.Column("end_time", sa.DateTime()),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("duration_samples", sa.Integer(), nullable=False),
        sa.Column("hr_mean", sa.Float()),
        sa.Column("hr_std", sa.Float()),
        sa.Column("hr_min", sa.Integer()),
        sa.Column("hr_max", sa.Integer()),
        sa.Column("hr_median", sa.Float()),
        sa.Column("cadence_mean", sa.Float()),
        sa.Column("cadence_std", sa.Float()),
        sa.Column("cadence_min", sa.Float()),
        sa.Column("cadence_max", sa.Float()),
        sa.Column("power_mean", sa.Float()),
        sa.Column("power_std", sa.Float()),
        sa.Column("power_min", sa.Float()),
        sa.Column("power_max", sa.Float()),
        sa.Column("penalty", sa.Float()),
        sa.Column("model", sa.String()),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        ),
    )

    # Re-create workout_metadata table
    op.create_table(
        "workout_metadata",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("activity_id", sa.String(), nullable=False, unique=True),
        sa.Column("rpe", sa.Integer()),
        sa.Column("feeling", sa.String()),
        sa.Column("mood", sa.String()),
        sa.Column("session_structure", sa.JSON()),
        sa.Column("focus_areas", sa.JSON()),
        sa.Column("notes", sa.Text()),
        sa.Column("lessons_learned", sa.Text()),
        sa.Column("planned_workout", sa.String()),
        sa.Column("deviations", sa.Text()),
        sa.Column("recovery_notes", sa.Text()),
        sa.Column("sleep_quality", sa.Integer()),
        sa.Column("stress_level", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        ),
    )

    # Remove metrics_data column
    op.drop_column("activities", "metrics_data")
