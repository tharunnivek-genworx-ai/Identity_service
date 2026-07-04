"""add_qc_section_content_hashes

Revision ID: d0e1f2a3b4c5
Revises: c9d4e5f6a7b8
Create Date: 2026-07-04

Adds qcsectioncontenthashes JSONB column to studymaterialversions
for frozen QC set content lineage validation on resume and full QC entry.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: str | Sequence[str] | None = "c9d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS qcsectioncontenthashes JSONB NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("studymaterialversions", "qcsectioncontenthashes")
