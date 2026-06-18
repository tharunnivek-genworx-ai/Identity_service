"""add_qc_columns_to_quizzes

Revision ID: e070ed1b4375
Revises: d4f8a2c91e07
Create Date: 2026-06-18 15:28:37.092440

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e070ed1b4375"
down_revision: str | Sequence[str] | None = "d4f8a2c91e07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "quizzes",
        sa.Column(
            "qcfailedpermanently", sa.Boolean(), server_default="false", nullable=False
        ),
    )
    op.add_column(
        "quizzes",
        sa.Column("qcresult", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("quizzes", "qcresult")
    op.drop_column("quizzes", "qcfailedpermanently")
