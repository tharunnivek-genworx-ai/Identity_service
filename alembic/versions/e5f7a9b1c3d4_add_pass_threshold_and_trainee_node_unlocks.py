"""add pass_threshold_percent and trainee_node_unlocks

Revision ID: e5f7a9b1c3d4
Revises: d4e6f8a0b2c3
Create Date: 2026-07-18

Adds quizzes.passthresholdpercent (default 70, 1–100) and durable
traineenodeunlocks grants for progressive subtopic unlocking.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e5f7a9b1c3d4"
down_revision: str | Sequence[str] | None = "d4e6f8a0b2c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "quizzes",
        sa.Column(
            "passthresholdpercent",
            sa.Integer(),
            nullable=False,
            server_default="70",
        ),
    )
    op.create_check_constraint(
        "ck_quizzes_passthresholdpercent",
        "quizzes",
        "passthresholdpercent >= 1 AND passthresholdpercent <= 100",
    )

    op.create_table(
        "traineenodeunlocks",
        sa.Column("unlockid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("traineeid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nodeid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("spaceid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "unlockedat",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("gatenodeid", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["gatenodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["nodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["spaceid"], ["espaces.spaceid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["traineeid"], ["trainees.traineeid"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("unlockid"),
        sa.UniqueConstraint(
            "traineeid", "nodeid", name="uq_traineenodeunlocks_trainee_node"
        ),
    )
    op.create_index(
        "ix_traineenodeunlocks_nodeid",
        "traineenodeunlocks",
        ["nodeid"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_traineenodeunlocks_nodeid", table_name="traineenodeunlocks")
    op.drop_table("traineenodeunlocks")
    op.drop_constraint("ck_quizzes_passthresholdpercent", "quizzes", type_="check")
    op.drop_column("quizzes", "passthresholdpercent")
