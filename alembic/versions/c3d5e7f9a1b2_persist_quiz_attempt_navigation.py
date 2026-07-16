"""persist trainee quiz attempt navigation

Revision ID: c3d5e7f9a1b2
Revises: b2c4d6e8f0a1
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c3d5e7f9a1b2"
down_revision: str | Sequence[str] | None = "b2c4d6e8f0a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "quizquestionresponses",
        sa.Column("isvisited", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "quizquestionresponses",
        sa.Column("isflagged", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "quizattempts",
        sa.Column("resumequestionid", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_quizattempts_resumequestionid_quizquestions",
        "quizattempts",
        "quizquestions",
        ["resumequestionid"],
        ["questionid"],
        ondelete="SET NULL",
    )

    # Preserve the newest active attempt and freeze deterministic older duplicates
    # before installing the race-proof partial unique index.
    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT attemptid,
                       row_number() OVER (
                           PARTITION BY quizid, traineeid
                           ORDER BY startedat DESC, attemptid DESC
                       ) AS rn
                FROM quizattempts
                WHERE status = 'in_progress'
            )
            UPDATE quizattempts AS qa
            SET status = 'abandoned'
            FROM ranked
            WHERE qa.attemptid = ranked.attemptid
              AND ranked.rn > 1
            """
        )
    )
    op.create_index(
        "uq_quizattempts_one_in_progress_per_quiz_trainee",
        "quizattempts",
        ["quizid", "traineeid"],
        unique=True,
        postgresql_where=sa.text("status = 'in_progress'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_quizattempts_one_in_progress_per_quiz_trainee",
        table_name="quizattempts",
    )
    op.drop_constraint(
        "fk_quizattempts_resumequestionid_quizquestions",
        "quizattempts",
        type_="foreignkey",
    )
    op.drop_column("quizattempts", "resumequestionid")
    op.drop_column("quizquestionresponses", "isflagged")
    op.drop_column("quizquestionresponses", "isvisited")
