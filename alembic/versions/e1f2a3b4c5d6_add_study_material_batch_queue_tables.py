"""add_study_material_batch_queue_tables

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-07-08

Adds studymaterialbatchruns and studymaterialbatchitems queue tables for
space-level generate-all orchestration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: str | Sequence[str] | None = "d0e1f2a3b4c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "studymaterialbatchruns",
        sa.Column("batchid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("spaceid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mentorid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("queueposition", sa.Integer(), nullable=False),
        sa.Column(
            "selectedrootnodeids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "policy",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("totalitems", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completeditems", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("faileditems", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skippeditems", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currentitemid", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_studymaterialbatchruns_status",
        ),
        sa.ForeignKeyConstraint(
            ["mentorid"], ["mentors.mentorid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["spaceid"], ["espaces.spaceid"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("batchid"),
    )

    op.create_table(
        "studymaterialbatchitems",
        sa.Column("itemid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batchid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nodeid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rootsegmentnodeid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("depthlevel", sa.Integer(), nullable=False),
        sa.Column(
            "pathnodeids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "pathtitles",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("nodetitle", sa.String(length=300), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("generationrunid", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("versionid", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("errormessage", sa.Text(), nullable=True),
        sa.Column("completedat", sa.TIMESTAMP(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "status IN ("
            "'queued', "
            "'running', "
            "'completed', "
            "'failed', "
            "'failed_retryable', "
            "'skipped', "
            "'cancelled'"
            ")",
            name="ck_studymaterialbatchitems_status",
        ),
        sa.ForeignKeyConstraint(
            ["batchid"], ["studymaterialbatchruns.batchid"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["nodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["rootsegmentnodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["generationrunid"], ["generationruns.runid"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["versionid"], ["studymaterialversions.versionid"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("itemid"),
    )

    op.create_foreign_key(
        "fk_studymaterialbatchruns_currentitemid",
        source_table="studymaterialbatchruns",
        referent_table="studymaterialbatchitems",
        local_cols=["currentitemid"],
        remote_cols=["itemid"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_studymaterialbatchruns_space_status_queue",
        "studymaterialbatchruns",
        ["spaceid", "status", "queueposition"],
    )
    op.create_index(
        "ix_studymaterialbatchitems_batch_position",
        "studymaterialbatchitems",
        ["batchid", "position"],
    )
    op.create_index(
        "ix_studymaterialbatchruns_mentor_space_status",
        "studymaterialbatchruns",
        ["mentorid", "spaceid", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_studymaterialbatchruns_mentor_space_status",
        table_name="studymaterialbatchruns",
    )
    op.drop_index(
        "ix_studymaterialbatchitems_batch_position",
        table_name="studymaterialbatchitems",
    )
    op.drop_index(
        "ix_studymaterialbatchruns_space_status_queue",
        table_name="studymaterialbatchruns",
    )
    op.drop_constraint(
        "fk_studymaterialbatchruns_currentitemid",
        "studymaterialbatchruns",
        type_="foreignkey",
    )
    op.drop_table("studymaterialbatchitems")
    op.drop_table("studymaterialbatchruns")
