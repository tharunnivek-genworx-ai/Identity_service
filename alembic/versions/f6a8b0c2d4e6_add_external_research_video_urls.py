"""add videourls to externalresearchreference

Revision ID: f6a8b0c2d4e6
Revises: e5f7a9b1c3d4
Create Date: 2026-07-20

Stores ranked YouTube video metadata for external-research cache rows.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f6a8b0c2d4e6"
down_revision: str | Sequence[str] | None = "e5f7a9b1c3d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "externalresearchreference",
        sa.Column(
            "videourls",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("externalresearchreference", "videourls")
