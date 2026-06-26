"""add_content_lifecycle_columns

Revision ID: f3a1b2c4d5e6
Revises: e070ed1b4375
Create Date: 2026-06-20

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f3a1b2c4d5e6"
down_revision: str | Sequence[str] | None = "e070ed1b4375"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _backfill_lifecycle_status(table: str) -> None:
    # archived/hidden are set only by application transitions, not migration guesswork.
    op.execute(
        sa.text(
            f"""
            UPDATE {table}
            SET lifecyclestatus = CASE
                WHEN ispublished = true THEN 'active'
                ELSE 'draft'
            END
            """
        )
    )


def upgrade() -> None:
    op.add_column(
        "studymaterialversions",
        sa.Column(
            "lifecyclestatus",
            sa.String(length=20),
            nullable=False,
            server_default="draft",
        ),
    )
    op.add_column(
        "studymaterialversions",
        sa.Column("supersededat", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "studymaterialversions",
        sa.Column("pausedreason", sa.String(length=50), nullable=True),
    )

    op.add_column(
        "quizzes",
        sa.Column(
            "lifecyclestatus",
            sa.String(length=20),
            nullable=False,
            server_default="draft",
        ),
    )
    op.add_column(
        "quizzes",
        sa.Column("supersededat", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "quizzes",
        sa.Column("deactivatedby", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "quizzes",
        sa.Column("pausedreason", sa.String(length=50), nullable=True),
    )

    _backfill_lifecycle_status("studymaterialversions")
    _backfill_lifecycle_status("quizzes")


def downgrade() -> None:
    op.drop_column("quizzes", "pausedreason")
    op.drop_column("quizzes", "deactivatedby")
    op.drop_column("quizzes", "supersededat")
    op.drop_column("quizzes", "lifecyclestatus")

    op.drop_column("studymaterialversions", "pausedreason")
    op.drop_column("studymaterialversions", "supersededat")
    op.drop_column("studymaterialversions", "lifecyclestatus")
