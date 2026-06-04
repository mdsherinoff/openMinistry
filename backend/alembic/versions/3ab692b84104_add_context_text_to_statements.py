"""add context_text to statements

Revision ID: 3ab692b84104
Revises: b653010b719e
Create Date: 2026-06-04 19:44:48.314475

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3ab692b84104'
down_revision: Union[str, None] = 'b653010b719e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("ALTER TABLE statements ADD COLUMN IF NOT EXISTS context_text TEXT;")
    op.execute("ALTER TABLE statements ADD COLUMN IF NOT EXISTS article_context TEXT;")
    op.execute("ALTER TABLE statements ADD COLUMN IF NOT EXISTS queue_item_id INTEGER;")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'statements_queue_item_id_fkey'
            ) THEN
                ALTER TABLE statements
                ADD CONSTRAINT statements_queue_item_id_fkey
                FOREIGN KEY (queue_item_id) REFERENCES article_queue(id);
            END IF;
        END $$;
    """)

def downgrade() -> None:
    op.execute(
        "ALTER TABLE statements DROP CONSTRAINT IF EXISTS "
        "statements_queue_item_id_fkey;"
    )
    op.drop_column("statements", "context_text")
    op.drop_column("statements", "article_context")
    op.drop_column("statements", "queue_item_id")
