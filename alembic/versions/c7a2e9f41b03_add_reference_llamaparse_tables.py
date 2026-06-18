"""add_reference_llamaparse_tables

Revision ID: c7a2e9f41b03
Revises: 78cfdaa3ac8f
Create Date: 2026-06-18 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7a2e9f41b03"
down_revision: str | Sequence[str] | None = "78cfdaa3ac8f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "referencellamaparsepdf",
        sa.Column("llamaparsepdfid", sa.UUID(), nullable=False),
        sa.Column("referencematerialid", sa.UUID(), nullable=False),
        sa.Column("nodeid", sa.UUID(), nullable=False),
        sa.Column("spaceid", sa.UUID(), nullable=False),
        sa.Column("llamaparsejobid", sa.String(length=200), nullable=False),
        sa.Column("llamaparseparsejobid", sa.String(length=200), nullable=True),
        sa.Column("contenthash", sa.String(length=64), nullable=False),
        sa.Column(
            "structuredjson",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("formattedtext", sa.Text(), nullable=False),
        sa.Column("parsedby", sa.UUID(), nullable=False),
        sa.Column("createdat", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updatedat", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["nodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["parsedby"], ["mentors.mentorid"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["referencematerialid"],
            ["referencematerials.materialid"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["spaceid"], ["espaces.spaceid"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("llamaparsepdfid"),
        sa.UniqueConstraint(
            "referencematerialid",
            "nodeid",
            name="uq_referencellamaparsepdf_material_node",
        ),
    )
    op.create_index(
        "ix_referencellamaparsepdf_contenthash",
        "referencellamaparsepdf",
        ["contenthash"],
        unique=False,
    )

    op.create_table(
        "referencellamaparseimages",
        sa.Column("llamaparseimageid", sa.UUID(), nullable=False),
        sa.Column("llamaparsepdfid", sa.UUID(), nullable=False),
        sa.Column("referencematerialid", sa.UUID(), nullable=False),
        sa.Column("nodeid", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("filename", sa.String(length=300), nullable=False),
        sa.Column("fileurl", sa.Text(), nullable=False),
        sa.Column("sourcepagenumber", sa.Integer(), nullable=True),
        sa.Column("figureindexonpage", sa.Integer(), nullable=True),
        sa.Column("parseindex", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("orderindex", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["llamaparsepdfid"],
            ["referencellamaparsepdf.llamaparsepdfid"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["nodeid"], ["topicnodes.nodeid"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["referencematerialid"],
            ["referencematerials.materialid"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("llamaparseimageid"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("referencellamaparseimages")
    op.drop_index(
        "ix_referencellamaparsepdf_contenthash",
        table_name="referencellamaparsepdf",
    )
    op.drop_table("referencellamaparsepdf")
