"""drop stale statement search trigger

Revision ID: 9c1f4d7a2b6e
Revises: 3ab692b84104
Create Date: 2026-06-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c1f4d7a2b6e"
down_revision: Union[str, None] = "3ab692b84104"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS statement_search_vector_update ON statements;")
    op.execute("DROP FUNCTION IF EXISTS update_statement_search_vector;")


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'statements'
                AND column_name = 'search_vector'
            ) THEN
                CREATE OR REPLACE FUNCTION update_statement_search_vector()
                RETURNS trigger AS $fn$
                BEGIN
                    NEW.search_vector = to_tsvector(
                        'english',
                        COALESCE(NEW.statement_text, '')
                    );
                    RETURN NEW;
                END;
                $fn$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS statement_search_vector_update
                ON statements;

                CREATE TRIGGER statement_search_vector_update
                BEFORE INSERT OR UPDATE ON statements
                FOR EACH ROW EXECUTE FUNCTION update_statement_search_vector();
            END IF;
        END $$;
    """)
