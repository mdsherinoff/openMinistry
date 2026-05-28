"""
Test name detection on scraped articles.
Usage: python nlp/test_detection.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

from nlp.name_detector import NameDetector
from nlp.detection_service import process_undetected_articles
from database.config import get_session_factory
from database.models.article import Article


def test():
    print("🔍 Testing Name Detection\n")

    SessionLocal = get_session_factory()
    db = SessionLocal()

    # Test 1 — Load ministers
    print("Test 1: Loading ministers into detector")
    detector = NameDetector()
    detector.load_ministers(db)
    print(f"Loaded {len(detector.ministers)} ministers\n")

    # Test 2 — Test on sample text
    print("Test 2: Detection on sample text")
    sample_texts = [
        "Chief Minister V.D. Satheesan announced new housing scheme today.",
        "Health Minister Muraleedharan visited the hospital in Thrissur.",
        "The CM said that the government will strengthen public hospitals.",
        "Pinarayi Vijayan, the Leader of Opposition, criticised the government.",
        "Finance Minister announced budget allocations for education sector.",
        "No ministers mentioned in this article about cricket.",
    ]

    for text in sample_texts:
        mentions = detector.detect_mentions(text)
        summary = detector.get_detection_summary(mentions)
        print(f"  Text: '{text[:60]}...'")
        if mentions:
            for m in mentions:
                print(
                    f"Found: {m['minister_name']} "
                    f"(via {m['match_type']}: '{m['matched_text']}')"
                )
        else:
            print(f"    — No ministers detected")
        print()

    # Test 3 — Run on actual database articles
    print("Test 3: Detection on database articles")
    total = db.query(Article).count()
    cleaned = db.query(Article).filter(
        Article.scrape_status == "cleaned"
    ).count()
    print(f"Total articles: {total}")
    print(f"Cleaned articles ready for detection: {cleaned}")

    if cleaned > 0:
        result = process_undetected_articles(db)
        print(f"\nDetection result: {result}")

        # Show detected articles
        detected = db.query(Article).filter(
            Article.scrape_status == "detected"
        ).all()
        print(f"\nArticles with minister mentions: {len(detected)}")
        for article in detected[:5]:
            print(f"  - {article.title[:70]}")
    else:
        print("No cleaned articles found — run the cleaner first")

    db.close()


if __name__ == "__main__":
    test()