"""drop_phase2_notification_chat_pdf_parse_tables

Revision ID: a7b2c9d4e5f6
Revises: 4d8e1a2b3c5f
Create Date: 2026-06-27

Drops unused phase-2 tables: chat, notifications, and pdf_parse_jobs.
Keeps progress tables, referencellamaparse*, and traineenodeprogress.chatsessioncount.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a7b2c9d4e5f6"
down_revision: str | Sequence[str] | None = "4d8e1a2b3c5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop children first (respect FK dependencies from ec1dd70e33e8).
    op.drop_table("chatmessages")
    op.drop_table("chatsessions")
    op.drop_table("pdfparsejobnodes")
    op.drop_table("pdfparsejobs")
    op.drop_index(
        "ix_nodeeventnotifications_space_node_created",
        table_name="nodeeventnotifications",
    )
    op.drop_table("nodeeventnotifications")
    op.drop_index(
        "ix_traineenotificationreads_trainee_type",
        table_name="traineenotificationreads",
    )
    op.drop_table("traineenotificationreads")
    op.drop_index(
        "ix_spaceannouncements_space_created",
        table_name="spaceannouncements",
    )
    op.drop_table("spaceannouncements")


def downgrade() -> None:
    # Recreate in dependency order (same DDL as ec1dd70e33e8).
    op.create_table(
        "traineenotificationreads",
        sa.Column("readid", sa.UUID(), nullable=False),
        sa.Column("traineeid", sa.UUID(), nullable=False),
        sa.Column("notificationtype", sa.String(length=20), nullable=False),
        sa.Column("notificationid", sa.UUID(), nullable=False),
        sa.Column("readat", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["traineeid"], ["trainees.traineeid"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("readid"),
        sa.UniqueConstraint(
            "traineeid",
            "notificationtype",
            "notificationid",
            name="uq_traineenotificationreads_trainee_type_notification",
        ),
    )
    op.create_index(
        "ix_traineenotificationreads_trainee_type",
        "traineenotificationreads",
        ["traineeid", "notificationtype"],
        unique=False,
    )

    op.create_table(
        "spaceannouncements",
        sa.Column("announcementid", sa.UUID(), nullable=False),
        sa.Column("spaceid", sa.UUID(), nullable=False),
        sa.Column("mentorid", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("eventtype", sa.String(length=50), nullable=False),
        sa.Column("createdat", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updatedat", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("isactive", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["mentorid"], ["mentors.mentorid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["spaceid"], ["espaces.spaceid"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("announcementid"),
    )
    op.create_index(
        "ix_spaceannouncements_space_created",
        "spaceannouncements",
        ["spaceid", "createdat"],
        unique=False,
    )

    op.create_table(
        "pdfparsejobs",
        sa.Column("jobid", sa.UUID(), nullable=False),
        sa.Column("spaceid", sa.UUID(), nullable=False),
        sa.Column("materialid", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("rawjson", sa.Text(), nullable=True),
        sa.Column("cleanedskeleton", sa.Text(), nullable=True),
        sa.Column("errormessage", sa.Text(), nullable=True),
        sa.Column("initiatedby", sa.UUID(), nullable=False),
        sa.Column("createdat", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updatedat", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["initiatedby"], ["mentors.mentorid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["materialid"], ["referencematerials.materialid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["spaceid"], ["espaces.spaceid"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("jobid"),
    )

    op.create_table(
        "chatsessions",
        sa.Column("sessionid", sa.UUID(), nullable=False),
        sa.Column("traineeid", sa.UUID(), nullable=False),
        sa.Column("nodeid", sa.UUID(), nullable=False),
        sa.Column("spaceid", sa.UUID(), nullable=False),
        sa.Column("studymaterialversionid", sa.UUID(), nullable=False),
        sa.Column("sessiontitle", sa.String(length=300), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("totalmessages", sa.Integer(), nullable=False),
        sa.Column("contexttokencount", sa.Integer(), nullable=True),
        sa.Column("startedat", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("lastmessageat", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("closedat", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["nodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["spaceid"], ["espaces.spaceid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["studymaterialversionid"],
            ["studymaterialversions.versionid"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["traineeid"], ["trainees.traineeid"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("sessionid"),
    )

    op.create_table(
        "pdfparsejobnodes",
        sa.Column("previewnodeid", sa.UUID(), nullable=False),
        sa.Column("jobid", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("orderindex", sa.Integer(), nullable=False),
        sa.Column("mentoraction", sa.String(length=20), nullable=False),
        sa.Column("appliednodeid", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["appliednodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["jobid"], ["pdfparsejobs.jobid"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("previewnodeid"),
    )

    op.create_table(
        "chatmessages",
        sa.Column("messageid", sa.UUID(), nullable=False),
        sa.Column("sessionid", sa.UUID(), nullable=False),
        sa.Column("traineeid", sa.UUID(), nullable=False),
        sa.Column("nodeid", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tokencount", sa.Integer(), nullable=True),
        sa.Column("llmmodelused", sa.String(length=100), nullable=True),
        sa.Column("contextwindowsnapshot", sa.Text(), nullable=True),
        sa.Column("createdat", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("isdeleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["nodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["sessionid"], ["chatsessions.sessionid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["traineeid"], ["trainees.traineeid"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("messageid"),
    )

    op.create_table(
        "nodeeventnotifications",
        sa.Column("notificationid", sa.UUID(), nullable=False),
        sa.Column("spaceid", sa.UUID(), nullable=False),
        sa.Column("nodeid", sa.UUID(), nullable=False),
        sa.Column("eventtype", sa.String(length=60), nullable=False),
        sa.Column("triggeredby", sa.UUID(), nullable=False),
        sa.Column("relatedversionid", sa.UUID(), nullable=True),
        sa.Column("relatedquizid", sa.UUID(), nullable=True),
        sa.Column("relatedmaterialid", sa.UUID(), nullable=True),
        sa.Column("systemmessage", sa.Text(), nullable=False),
        sa.Column("mentorcustommessage", sa.Text(), nullable=True),
        sa.Column("createdat", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["nodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["relatedmaterialid"],
            ["referencematerials.materialid"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["relatedquizid"], ["quizzes.quizid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["relatedversionid"],
            ["studymaterialversions.versionid"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["spaceid"], ["espaces.spaceid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["triggeredby"], ["mentors.mentorid"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("notificationid"),
    )
    op.create_index(
        "ix_nodeeventnotifications_space_node_created",
        "nodeeventnotifications",
        ["spaceid", "nodeid", "createdat"],
        unique=False,
    )
