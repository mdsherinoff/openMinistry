"""add public flagging fields to statements

Revision ID: a1f3c9d2e4b7
Revises: 9c1f4d7a2b6e
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1f3c9d2e4b7"
down_revision: Union[str, None] = "9c1f4d7a2b6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE statements "
        "ADD COLUMN IF NOT EXISTS flagged BOOLEAN NOT NULL DEFAULT FALSE;"
    )
    op.execute(
        "ALTER TABLE statements "
        "ADD COLUMN IF NOT EXISTS flag_count INTEGER NOT NULL DEFAULT 0;"
    )
    op.execute(
        "ALTER TABLE statements ADD COLUMN IF NOT EXISTS flag_reason TEXT;"
    )
    op.execute(
        "ALTER TABLE statements "
        "ADD COLUMN IF NOT EXISTS flagged_at TIMESTAMPTZ;"
    )
    # Partial index so the moderator "flagged" query stays fast.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_statements_flagged "
        "ON statements (flagged) WHERE flagged = TRUE;"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_statements_flagged;")
    op.drop_column("statements", "flagged_at")
    op.drop_column("statements", "flag_reason")
    op.drop_column("statements", "flag_count")
    op.drop_column("statements", "flagged")
