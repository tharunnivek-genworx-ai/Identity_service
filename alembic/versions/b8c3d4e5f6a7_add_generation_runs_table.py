"""add_generation_runs_table

Revision ID: b8c3d4e5f6a7
Revises: a7b2c9d4e5f6
Create Date: 2026-06-28

Adds generationruns table for durable cross-request generation checkpoints.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b8c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a7b2c9d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "generationruns",
        sa.Column("runid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pipeline", sa.String(length=30), nullable=False),
        sa.Column("resourcetype", sa.String(length=20), nullable=False),
        sa.Column("resourceid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nodeid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("spaceid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mentorid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="running"
        ),
        sa.Column("lastcompletednode", sa.String(length=80), nullable=True),
        sa.Column(
            "checkpointstate", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "requestparams", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("generationmode", sa.String(length=20), nullable=False),
        sa.Column("artifactrunid", sa.String(length=32), nullable=True),
        sa.Column(
            "progressstepindex",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("errormessage", sa.Text(), nullable=True),
        sa.Column("errortype", sa.String(length=80), nullable=True),
        sa.Column("nextllmretryat", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "attemptcount",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "createdat",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updatedat",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completedat", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["mentorid"], ["mentors.mentorid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["nodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["spaceid"], ["espaces.spaceid"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("runid"),
    )

    op.create_index(
        "ix_generationruns_node_pipeline_active",
        "generationruns",
        ["nodeid", "pipeline"],
        postgresql_where=sa.text("status IN ('running', 'failed')"),
    )
    op.create_index(
        "ix_generationruns_resource_pipeline_active",
        "generationruns",
        ["resourceid", "pipeline"],
        postgresql_where=sa.text("status IN ('running', 'failed')"),
    )
    op.create_index(
        "ix_generationruns_runid_status",
        "generationruns",
        ["runid", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_generationruns_runid_status", table_name="generationruns")
    op.drop_index(
        "ix_generationruns_resource_pipeline_active",
        table_name="generationruns",
    )
    op.drop_index(
        "ix_generationruns_node_pipeline_active",
        table_name="generationruns",
    )
    op.drop_table("generationruns")
