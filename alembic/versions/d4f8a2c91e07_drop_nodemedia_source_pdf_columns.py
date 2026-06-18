"""drop_nodemedia_source_pdf_columns

Revision ID: d4f8a2c91e07
Revises: c7a2e9f41b03
Create Date: 2026-06-18 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4f8a2c91e07"
down_revision: str | Sequence[str] | None = "c7a2e9f41b03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove legacy LlamaParse linkage columns from nodemedia."""
    op.drop_constraint(
        "nodemedia_sourcepdfmaterialid_fkey",
        "nodemedia",
        type_="foreignkey",
    )
    op.drop_column("nodemedia", "sourcepdfmaterialid")
    op.drop_column("nodemedia", "sourcepagenumber")


def downgrade() -> None:
    """Restore legacy LlamaParse linkage columns on nodemedia."""
    op.add_column(
        "nodemedia",
        sa.Column("sourcepagenumber", sa.Integer(), nullable=True),
    )
    op.add_column(
        "nodemedia",
        sa.Column("sourcepdfmaterialid", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "nodemedia_sourcepdfmaterialid_fkey",
        "nodemedia",
        "referencematerials",
        ["sourcepdfmaterialid"],
        ["materialid"],
        ondelete="RESTRICT",
    )
