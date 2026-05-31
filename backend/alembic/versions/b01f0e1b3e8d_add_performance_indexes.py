"""add performance indexes

Revision ID: b01f0e1b3e8d
Revises: ef8ebdfc62a3
Create Date: 2026-05-31 04:44:51.737307

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b01f0e1b3e8d'
down_revision: Union[str, None] = 'ef8ebdfc62a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Index for filtering approved statements
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_statements_status
        ON statements(status);
    """)

    # Index for minister + status queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_statements_minister_status
        ON statements(minister_id, status);
    """)

    # Index for topic filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_statements_topic
        ON statements(topic);
    """)

    # Index for date ordering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_statements_date
        ON statements(statement_date DESC NULLS LAST);
    """)

    # Index for article status
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_status
        ON articles(scrape_status);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_statements_status;")
    op.execute("DROP INDEX IF EXISTS idx_statements_minister_status;")
    op.execute("DROP INDEX IF EXISTS idx_statements_topic;")
    op.execute("DROP INDEX IF EXISTS idx_statements_date;")
    op.execute("DROP INDEX IF EXISTS idx_articles_status;")
