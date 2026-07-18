"""add externalresearchreference table

Revision ID: d4e6f8a0b2c3
Revises: c3d5e7f9a1b2
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d4e6f8a0b2c3"
down_revision: str | Sequence[str] | None = "c3d5e7f9a1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "externalresearchreference",
        sa.Column("externalresearchid", sa.UUID(), nullable=False),
        sa.Column("nodeid", sa.UUID(), nullable=False),
        sa.Column("spaceid", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("failreason", sa.String(length=100), nullable=True),
        sa.Column("searchqueryused", sa.Text(), nullable=True),
        sa.Column("resolvedtopic", sa.Text(), nullable=True),
        sa.Column("resolvedsubtopic", sa.Text(), nullable=True),
        sa.Column("groundtruthreference", sa.Text(), nullable=True),
        sa.Column(
            "sourceurls",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "perwebsitesummarycount",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("tokencount", sa.Integer(), nullable=True),
        sa.Column("knowledgedistillationmodelused", sa.Text(), nullable=True),
        sa.Column("requestedby", sa.UUID(), nullable=False),
        sa.Column("createdat", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["nodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["requestedby"], ["mentors.mentorid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["spaceid"], ["espaces.spaceid"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("externalresearchid"),
        sa.UniqueConstraint("nodeid", name="uq_externalresearchreference_node"),
    )
    op.create_index(
        "ix_externalresearchreference_spaceid",
        "externalresearchreference",
        ["spaceid"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_externalresearchreference_spaceid",
        table_name="externalresearchreference",
    )
    op.drop_table("externalresearchreference")
