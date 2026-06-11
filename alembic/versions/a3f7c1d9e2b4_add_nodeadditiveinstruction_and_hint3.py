"""add_nodeadditiveinstruction_and_hint3

Revision ID: a3f7c1d9e2b4
Revises: f112db9fd196
Create Date: 2026-06-10 09:04:00.000000

Adds:
  - topicnodes.nodeadditiveinstruction TEXT NULL
      Additive instruction for a single node only. Applied on top of inherited
      treedefaultinstruction values from ancestors. NOT inherited by descendants.
      Resolution order:
        1. nodespecificinstruction (full override, if set)
        2. inherited treedefaultinstruction chain + this node's nodeadditiveinstruction

  - quizquestions.hint3 TEXT NULL
      Third progressive hint. Most explicit hint possible, but does NOT reveal the
      correct answer. Revealed on the 3rd consecutive wrong attempt (hint_level_reached=3).
      hint1 → subtle nudge (1st wrong)
      hint2 → narrows reasoning (2nd wrong)
      hint3 → most explicit, still no answer reveal (3rd wrong)
      explanation → post-submit review only, never during a live attempt
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f7c1d9e2b4'
down_revision: Union[str, Sequence[str], None] = 'f112db9fd196'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ── topicnodes: add nodeadditiveinstruction ──────────────────────────────
    op.add_column(
        "topicnodes",
        sa.Column("nodeadditiveinstruction", sa.Text(), nullable=True),
    )

    # ── quizquestions: add hint3 ─────────────────────────────────────────────
    op.add_column(
        "quizquestions",
        sa.Column("hint3", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("quizquestions", "hint3")
    op.drop_column("topicnodes", "nodeadditiveinstruction")
