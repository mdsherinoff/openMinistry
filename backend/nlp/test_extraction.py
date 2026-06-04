"""
Test quote extraction pipeline.
Usage: python nlp/test_extraction.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.WARNING)

from nlp.quote_extractor import QuoteExtractor
from backend.nlp.miner_pipeline import run_pipeline
from database.config import get_session_factory
from database.models.statement import Statement
from database.models.article import Article


def test():
    print("📝 Testing Quote Extraction\n")
    extractor = QuoteExtractor()

    # Test 1 — Direct quotes
    print("Test 1: Direct quote extraction")
    sample = """
    Chief Minister V.D. Satheesan inaugurated the new hospital today.
    "We will ensure every citizen has access to quality healthcare,"
    the Chief Minister said at the event in Thiruvananthapuram.
    He added that the government has allocated 500 crore rupees
    for the health sector this year.
    Satheesan stated that more hospitals would be built in rural areas.
    """

    quotes = extractor.extract_quotes(sample, "V. D. Satheesan")
    print(f"Found {len(quotes)} quotes:")
    for q in quotes:
        print(f"  [{q.quote_type}] ({q.confidence:.2f}) {q.text[:100]}...")
    print()

    # Test 2 — Indirect quotes
    print("Test 2: Indirect quote extraction")
    sample2 = """
    Health Minister Muraleedharan said that the dengue outbreak
    was under control. The minister stated that 50 new health
    centres would be opened across the state. He mentioned that
    special teams have been deployed in affected districts.
    """

    quotes2 = extractor.extract_quotes(sample2, "K. Muraleedharan")
    print(f"Found {len(quotes2)} quotes:")
    for q in quotes2:
        print(f"  [{q.quote_type}] ({q.confidence:.2f}) {q.text[:100]}...")
    print()

    # Test 3 — Run full pipeline on database
    print("Test 3: Full pipeline on database articles")
    SessionLocal = get_session_factory()
    db = SessionLocal()

    total_articles = db.query(Article).count()
    pending_statements = db.query(Statement).filter(
        Statement.status == "pending"
    ).count()

    print(f"Articles in DB: {total_articles}")
    print(f"Existing pending statements: {pending_statements}")

    result = run_pipeline(db)
    print(f"\n✅ Pipeline result: {result}")

    # Show sample statements
    statements = db.query(Statement).filter(
        Statement.status == "pending"
    ).limit(5).all()

    print(f"\nSample statements created:")
    for stmt in statements:
        print(f"  Minister ID: {stmt.minister_id}")
        print(f"  Confidence: {stmt.confidence_score:.2f}")
        print(f"  Text: {stmt.statement_text[:120]}...")
        print()

    db.close()


if __name__ == "__main__":
    test()