"""
Test duplicate detection.
Usage: python scrapers/test_duplicates.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

from scrapers.duplicate_detector import DuplicateDetector
from scrapers.sources.the_hindu import TheHinduScraper
from scrapers.article_store import save_articles
from database.config import get_session_factory


def test():
    print("Testing Duplicate Detection\n")
    detector = DuplicateDetector()

    # Test 1 — URL hash consistency
    print("Test 1: URL hash consistency")
    url = "https://www.thehindu.com/news/national/kerala/test-article/article123.ece"
    hash1 = detector.make_url_hash(url)
    hash2 = detector.make_url_hash(url + "?utm_source=google")
    print(f"Hash without params: {hash1[:20]}...")
    print(f"Hash with params:    {hash2[:20]}...")
    print(f"Hashes match (should be True): {hash1 == hash2}\n")

    # Test 2 — Title similarity
    print("Test 2: Title similarity")
    pairs = [
        ("Kerala CM announces new policy", "Kerala CM announces new policy"),
        ("Kerala CM announces new policy", "Kerala CM announces new policies"),
        ("Kerala CM announces new policy", "Delhi weather forecast today"),
    ]
    for t1, t2 in pairs:
        sim = detector._title_similarity(t1, t2)
        print(f"  '{t1[:40]}' vs '{t2[:40]}' → {sim:.2f}")

    # Test 3 — Run scraper twice, second run should all be duplicates
    print("\nTest 3: Scrape same source twice")
    SessionLocal = get_session_factory()
    db = SessionLocal()

    print("First scrape...")
    scraper = TheHinduScraper()
    urls = scraper.get_article_urls()
    article_urls = [u for u in urls if "/article" in u][:5]

    articles = []
    for url in article_urls:
        article = scraper.scrape_article(url)
        if article:
            articles.append(article)

    result1 = save_articles(articles, db)
    print(f"First run: {result1}")

    print("\nSecond scrape (same articles)...")
    result2 = save_articles(articles, db)
    print(f"Second run: {result2}")
    print(
        f"All duplicates detected: "
        f"{result2['skipped_duplicate'] == len(articles)}"
    )

    db.close()


if __name__ == "__main__":
    test()