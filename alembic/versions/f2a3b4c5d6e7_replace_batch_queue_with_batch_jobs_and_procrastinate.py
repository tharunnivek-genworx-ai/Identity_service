"""replace_batch_queue_with_batch_jobs_and_procrastinate

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-07-11

Drops legacy studymaterialbatch* queue tables, creates lean batch_jobs /
batch_job_steps tables, and installs the Procrastinate 3.9.0 job queue schema.
"""

from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f2a3b4c5d6e7"
down_revision: str | Sequence[str] | None = "e1f2a3b4c5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def _load_sql(filename: str) -> str:
    return (_SQL_DIR / filename).read_text(encoding="utf-8")


def _execute_sql_file(filename: str) -> None:
    connection = op.get_bind()
    connection.execute(sa.text(_load_sql(filename)))


def _drop_legacy_batch_tables() -> None:
    op.drop_constraint(
        "fk_studymaterialbatchruns_currentitemid",
        "studymaterialbatchruns",
        type_="foreignkey",
    )
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
    op.drop_table("studymaterialbatchitems")
    op.drop_table("studymaterialbatchruns")


def _create_batch_jobs_tables() -> None:
    op.create_table(
        "batch_jobs",
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mentor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "policy",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "selected_root_node_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_steps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_batch_jobs_status",
        ),
        sa.ForeignKeyConstraint(
            ["mentor_id"], ["mentors.mentorid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["space_id"], ["espaces.spaceid"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("batch_id"),
    )

    op.create_table(
        "batch_job_steps",
        sa.Column("step_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_title", sa.Text(), nullable=False),
        sa.Column(
            "path_titles",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("depth_level", sa.Integer(), nullable=False),
        sa.Column(
            "root_segment_node_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("generation_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'skipped')",
            name="ck_batch_job_steps_status",
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"], ["batch_jobs.batch_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["node_id"], ["topicnodes.nodeid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["root_segment_node_id"], ["topicnodes.nodeid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["generation_run_id"], ["generationruns.runid"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("step_id"),
        sa.UniqueConstraint(
            "batch_id", "position", name="uq_batch_job_steps_batch_position"
        ),
    )

    op.create_index(
        "ix_batch_jobs_space_status",
        "batch_jobs",
        ["space_id", "status"],
    )
    op.create_index(
        "ix_batch_job_steps_batch_status",
        "batch_job_steps",
        ["batch_id", "status"],
    )


def _recreate_legacy_batch_tables() -> None:
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


def upgrade() -> None:
    _drop_legacy_batch_tables()
    _create_batch_jobs_tables()
    _execute_sql_file("procrastinate_schema_v3_9_0.sql")


def downgrade() -> None:
    _execute_sql_file("procrastinate_schema_downgrade_v3_9_0.sql")
    op.drop_index("ix_batch_job_steps_batch_status", table_name="batch_job_steps")
    op.drop_index("ix_batch_jobs_space_status", table_name="batch_jobs")
    op.drop_table("batch_job_steps")
    op.drop_table("batch_jobs")
    _recreate_legacy_batch_tables()
