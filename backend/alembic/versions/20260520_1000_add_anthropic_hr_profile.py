"""Add anthropic_hr_profile column to activities

Revision ID: 005
Revises: 004
Create Date: 2026-05-20 10:00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activities", sa.Column("anthropic_hr_profile", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("activities", "anthropic_hr_profile")
