"""add_generation_outcome_columns

Revision ID: c9d4e5f6a7b8
Revises: b8c3d4e5f6a7
Create Date: 2026-07-02

Adds generation outcome routing columns to studymaterialversions for
explicit classifier outcomes, detail JSONB, and QC evaluation flag.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c9d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b8c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS generationoutcome VARCHAR(32) NULL"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS generationoutcomedetail JSONB NULL"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS qcevaluated BOOLEAN NOT NULL DEFAULT false"
        )
    )


def downgrade() -> None:
    op.drop_column("studymaterialversions", "qcevaluated")
    op.drop_column("studymaterialversions", "generationoutcomedetail")
    op.drop_column("studymaterialversions", "generationoutcome")
