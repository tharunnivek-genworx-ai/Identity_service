"""add_generation_run_lifecycle_columns

Revision ID: a1b2c3d4e5f8
Revises: f2a3b4c5d6e7
Create Date: 2026-07-12

Adds pause/abandon lifecycle columns, execution token, request fingerprint,
LlamaParse audit job IDs, and updates partial indexes for active run lookups.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a1b2c3d4e5f8"
down_revision: str | Sequence[str] | None = "f2a3b4c5d6e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "generationruns",
        sa.Column("pausedat", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "generationruns",
        sa.Column("abandonedat", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "generationruns",
        sa.Column("pausereason", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "generationruns",
        sa.Column("abandonreason", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "generationruns",
        sa.Column("requestfingerprint", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "generationruns",
        sa.Column(
            "executiontoken",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "generationruns",
        sa.Column("llamaparseextractjobid", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "generationruns",
        sa.Column("llamaparseparsejobid", sa.String(length=80), nullable=True),
    )

    op.drop_index(
        "ix_generationruns_node_pipeline_active",
        table_name="generationruns",
    )
    op.drop_index(
        "ix_generationruns_resource_pipeline_active",
        table_name="generationruns",
    )
    op.create_index(
        "ix_generationruns_node_pipeline_active",
        "generationruns",
        ["nodeid", "pipeline"],
        postgresql_where=sa.text("status IN ('running', 'failed', 'paused')"),
    )
    op.create_index(
        "ix_generationruns_resource_pipeline_active",
        "generationruns",
        ["resourceid", "pipeline"],
        postgresql_where=sa.text("status IN ('running', 'failed', 'paused')"),
    )
    op.create_index(
        "ix_generationruns_status_updatedat",
        "generationruns",
        ["status", "updatedat"],
    )

    op.execute(
        sa.text(
            """
            UPDATE generationruns
            SET status = 'abandoned',
                abandonedat = COALESCE(abandonedat, updatedat, NOW()),
                abandonreason = COALESCE(abandonreason, 'legacy_cancelled')
            WHERE status = 'cancelled'
            """
        )
    )


def downgrade() -> None:
    op.drop_index(
        "ix_generationruns_status_updatedat",
        table_name="generationruns",
    )
    op.drop_index(
        "ix_generationruns_resource_pipeline_active",
        table_name="generationruns",
    )
    op.drop_index(
        "ix_generationruns_node_pipeline_active",
        table_name="generationruns",
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

    op.drop_column("generationruns", "llamaparseparsejobid")
    op.drop_column("generationruns", "llamaparseextractjobid")
    op.drop_column("generationruns", "executiontoken")
    op.drop_column("generationruns", "requestfingerprint")
    op.drop_column("generationruns", "abandonreason")
    op.drop_column("generationruns", "pausereason")
    op.drop_column("generationruns", "abandonedat")
    op.drop_column("generationruns", "pausedat")
