"""Add splits_data column to activities

Revision ID: 003
Revises: 002
Create Date: 2026-05-20 09:00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add splits_data JSON column to activities table
    op.add_column("activities", sa.Column("splits_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove splits_data column
    op.drop_column("activities", "splits_data")
