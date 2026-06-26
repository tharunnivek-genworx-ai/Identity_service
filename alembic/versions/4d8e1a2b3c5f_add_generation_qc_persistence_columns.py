"""add_generation_qc_persistence_columns

Revision ID: 4d8e1a2b3c5f
Revises: 3c5e7f9a1b2d
Create Date: 2026-06-26

Adds generation/QC persistence columns to studymaterialversions and
nextllmretryat to both studymaterialversions and quizzes (replacing the
ad-hoc SQL migration script).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4d8e1a2b3c5f"
down_revision: str | Sequence[str] | None = "3c5e7f9a1b2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Idempotent adds — safe when nextllmretryat was applied via ad-hoc SQL earlier.
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS nextllmretryat TIMESTAMPTZ NULL"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE quizzes "
            "ADD COLUMN IF NOT EXISTS nextllmretryat TIMESTAMPTZ NULL"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS qcpassed BOOLEAN NOT NULL DEFAULT false"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS qcattemptcount INTEGER NOT NULL DEFAULT 0"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS generationrunid VARCHAR(32) NULL"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS conceptplan JSONB NULL"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS checklistllmmodelused VARCHAR(100) NULL"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS qcverificationmode VARCHAR(20) NULL"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS qcfrozencheckids JSONB NULL"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE studymaterialversions "
            "ADD COLUMN IF NOT EXISTS qcfrozensectionkeys JSONB NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("studymaterialversions", "qcfrozensectionkeys")
    op.drop_column("studymaterialversions", "qcfrozencheckids")
    op.drop_column("studymaterialversions", "qcverificationmode")
    op.drop_column("studymaterialversions", "checklistllmmodelused")
    op.drop_column("studymaterialversions", "conceptplan")
    op.drop_column("studymaterialversions", "generationrunid")
    op.drop_column("studymaterialversions", "qcattemptcount")
    op.drop_column("studymaterialversions", "qcpassed")
    op.drop_column("studymaterialversions", "nextllmretryat")
    op.drop_column("quizzes", "nextllmretryat")
