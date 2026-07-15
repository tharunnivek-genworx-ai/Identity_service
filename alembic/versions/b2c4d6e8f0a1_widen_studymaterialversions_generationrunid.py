"""widen studymaterialversions.generationrunid to hold a durable run UUID

Revision ID: b2c4d6e8f0a1
Revises: a1b2c3d4e5f8
Create Date: 2026-07-15

``generationrunid`` was created as VARCHAR(32) to store the legacy artifact
timestamp id. Durable generation runs now persist ``str(run_id)`` — a 36-char
UUID string — which overflows VARCHAR(32) and raises
``StringDataRightTruncationError`` on version insert. Widen the column to
VARCHAR(64) so it comfortably holds a UUID string (and any legacy value).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b2c4d6e8f0a1"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ALTER COLUMN generationrunid TYPE VARCHAR(64)"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ALTER COLUMN generationrunid TYPE VARCHAR(32)"
        )
    )
