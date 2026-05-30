"""add fulltext search index

Revision ID: ef8ebdfc62a3
Revises: d4ea5ab49efa
Create Date: 2026-05-30 04:19:58.542366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef8ebdfc62a3'
down_revision: Union[str, None] = 'd4ea5ab49efa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tsvector column for full-text search
    op.execute("""
        ALTER TABLE statements 
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
    """)

    # Populate it
    op.execute("""
        UPDATE statements 
        SET search_vector = to_tsvector('english', 
            COALESCE(statement_text, '')
        );
    """)

    # Create GIN index for fast search
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_statements_search 
        ON statements USING GIN(search_vector);
    """)

    # Create trigger to auto-update search vector
    op.execute("""
        CREATE OR REPLACE FUNCTION update_statement_search_vector()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector = to_tsvector('english',
                COALESCE(NEW.statement_text, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS statement_search_vector_update 
        ON statements;
        
        CREATE TRIGGER statement_search_vector_update
        BEFORE INSERT OR UPDATE ON statements
        FOR EACH ROW EXECUTE FUNCTION update_statement_search_vector();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS statement_search_vector_update ON statements;")
    op.execute("DROP FUNCTION IF EXISTS update_statement_search_vector;")
    op.execute("DROP INDEX IF EXISTS idx_statements_search;")
    op.execute("ALTER TABLE statements DROP COLUMN IF EXISTS search_vector;")
