"""Add is_intervals and workout_structure columns to activities

Revision ID: 004
Revises: 003
Create Date: 2026-05-20 09:10:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("activities", sa.Column("is_intervals", sa.String(), nullable=True))
    op.add_column(
        "activities", sa.Column("workout_structure", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("activities", "workout_structure")
    op.drop_column("activities", "is_intervals")
