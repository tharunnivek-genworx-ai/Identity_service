"""add_treedefaultinstruction

Revision ID: 299c5dd0304e
Revises: ec1dd70e33e8
Create Date: 2026-06-09 11:29:59.426261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '299c5dd0304e'
down_revision: Union[str, Sequence[str], None] = 'ec1dd70e33e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("topicnodes", sa.Column("treedefaultinstruction", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("topicnodes", "treedefaultinstruction")

