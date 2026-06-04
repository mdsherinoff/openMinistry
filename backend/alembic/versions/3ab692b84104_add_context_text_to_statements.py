"""add context_text to statements

Revision ID: 3ab692b84104
Revises: b653010b719e
Create Date: 2026-06-04 19:44:48.314475

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3ab692b84104'
down_revision: Union[str, None] = 'b653010b719e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column(
        "statements",
        sa.Column("context_text", sa.Text(), nullable=True)
    )
    op.add_column(
        "statements",
        sa.Column("article_context", sa.Text(), nullable=True)
    )
    op.add_column(
        "statements",
        sa.Column(
            "queue_item_id",
            sa.Integer(),
            sa.ForeignKey("article_queue.id"),
            nullable=True
        )
    )

def downgrade() -> None:
    op.drop_column("statements", "context_text")
    op.drop_column("statements", "article_context")
    op.drop_column("statements", "queue_item_id")