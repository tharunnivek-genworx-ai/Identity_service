"""drop_defaultteachinginstruction

Revision ID: f112db9fd196
Revises: 299c5dd0304e
Create Date: 2026-06-09 11:30:10.230947

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f112db9fd196"
down_revision: str | Sequence[str] | None = "299c5dd0304e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("espaces", "defaultteachinginstruction")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "espaces", sa.Column("defaultteachinginstruction", sa.Text(), nullable=True)
    )
