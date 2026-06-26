"""relax_quiz_sm_version_fk_drop_obsolete_lifecycle_cols

Revision ID: 3c5e7f9a1b2d
Revises: f3a1b2c4d5e6
Create Date: 2026-06-22

Changes:
  - quizzes.studymaterialversionid: NOT NULL → NULL; FK ON DELETE RESTRICT → ON DELETE SET NULL
  - quizzes: drop pausedreason, deactivatedby columns
  - studymaterialversions: drop pausedreason column

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3c5e7f9a1b2d"
down_revision: str | Sequence[str] | None = "f3a1b2c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 0.1  Relax quiz → study-material-version FK ──────────────────────────
    # Drop existing RESTRICT FK (auto-named by Postgres on table creation).
    op.execute(
        sa.text(
            "ALTER TABLE quizzes "
            "DROP CONSTRAINT IF EXISTS quizzes_studymaterialversionid_fkey"
        )
    )

    # Allow NULL so a quiz can outlive a discarded source version.
    op.alter_column("quizzes", "studymaterialversionid", nullable=True)

    # Re-add FK as optional metadata reference with ON DELETE SET NULL.
    op.create_foreign_key(
        "quizzes_studymaterialversionid_fkey",
        "quizzes",
        "studymaterialversions",
        ["studymaterialversionid"],
        ["versionid"],
        ondelete="SET NULL",
    )

    # ── 0.2  Drop obsolete lifecycle columns ─────────────────────────────────
    # Clear before drop (no-op for existing NULLs; defensive for any stale data).
    op.execute(sa.text("UPDATE quizzes SET pausedreason = NULL, deactivatedby = NULL"))
    op.drop_column("quizzes", "pausedreason")
    op.drop_column("quizzes", "deactivatedby")

    op.execute(sa.text("UPDATE studymaterialversions SET pausedreason = NULL"))
    op.drop_column("studymaterialversions", "pausedreason")


def downgrade() -> None:
    # Restore studymaterialversions.pausedreason
    op.add_column(
        "studymaterialversions",
        sa.Column("pausedreason", sa.String(length=50), nullable=True),
    )

    # Restore quizzes columns
    op.add_column(
        "quizzes",
        sa.Column("deactivatedby", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "quizzes",
        sa.Column("pausedreason", sa.String(length=50), nullable=True),
    )

    # Restore original FK: drop SET NULL variant, make NOT NULL, re-add RESTRICT.
    # NOTE: downgrade will fail if any studymaterialversionid rows are NULL;
    # ensure all quiz rows have a valid version before downgrading.
    op.drop_constraint(
        "quizzes_studymaterialversionid_fkey", "quizzes", type_="foreignkey"
    )
    op.alter_column("quizzes", "studymaterialversionid", nullable=False)
    op.create_foreign_key(
        "quizzes_studymaterialversionid_fkey",
        "quizzes",
        "studymaterialversions",
        ["studymaterialversionid"],
        ["versionid"],
        ondelete="RESTRICT",
    )
