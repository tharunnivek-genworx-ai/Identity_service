"""add_study_material_version_archive

Revision ID: b4e8f2a1c3d5
Revises: a3f7c1d9e2b4
Create Date: 2026-06-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b4e8f2a1c3d5"
down_revision: str | Sequence[str] | None = "a3f7c1d9e2b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "studymaterialversions",
        sa.Column("isarchived", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "studymaterialversions",
        sa.Column("archivedat", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "studymaterialversions",
        sa.Column(
            "archivedby",
            sa.UUID(),
            sa.ForeignKey("mentors.mentorid", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.alter_column("studymaterialversions", "isarchived", server_default=None)


def downgrade() -> None:
    op.drop_column("studymaterialversions", "archivedby")
    op.drop_column("studymaterialversions", "archivedat")
    op.drop_column("studymaterialversions", "isarchived")
