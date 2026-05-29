"""
Test statement storage with quality checks.
Usage: python nlp/test_statement_store.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.WARNING)

from nlp.statement_store import StatementStore
from nlp.statement_pipeline import run_pipeline
from database.config import get_session_factory
from database.models.statement import Statement


def test():
    print("💾 Testing Statement Storage\n")
    store = StatementStore()

    # Test 1 — Quality checks
    print("Test 1: Quality checks")
    test_cases = [
        ("We will build 1000 hospitals across Kerala.", 0.8, True),
        ("Click here.", 0.8, False),
        ("Ok.", 0.9, False),
        ("The government will strengthen public hospitals said minister.", 0.7, True),
        ("Subscribe to our newsletter for more updates.", 0.8, False),
        ("We have allocated 500 crore rupees for health sector.", 0.65, True),
        ("short", 0.9, False),
    ]

    for text, confidence, expected in test_cases:
        is_quality, reason = store.is_quality_statement(text, confidence)
        status = "✅" if is_quality == expected else "❌"
        print(f"  {status} '{text[:50]}' → {is_quality} ({reason})")

    # Test 2 — Queue stats
    print("\nTest 2: Queue statistics")
    SessionLocal = get_session_factory()
    db = SessionLocal()
    stats = store.get_queue_stats(db)
    print(f"  Queue stats: {stats}")

    # Test 3 — Run pipeline
    print("\nTest 3: Running pipeline")
    result = run_pipeline(db)
    print(f"  Result: {result}")

    # Show sample high confidence statements
    print("\nTop 5 highest confidence statements:")
    statements = db.query(Statement).filter(
        Statement.status == "pending"
    ).order_by(
        Statement.confidence_score.desc()
    ).limit(5).all()

    for stmt in statements:
        print(f"  [{stmt.confidence_score:.2f}] {stmt.statement_text[:100]}...")

    db.close()


if __name__ == "__main__":
    test()