"""
QA tests for the scraping pipeline.
Usage: python scrapers/test_qa.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

from scrapers.base_scraper import BaseScraper
from scrapers.monitor import ScraperMonitor
from scrapers.cleaner import ArticleCleaner
from database.config import get_session_factory


def test_retry_logic():
    """Test that retry logic handles bad URLs gracefully."""
    print("\nTest 1: Retry logic on bad URLs")
    from scrapers.sources.the_hindu import TheHinduScraper
    scraper = TheHinduScraper()

    bad_urls = [
        "https://www.thehindu.com/news/national/kerala/this-does-not-exist/article999.ece",
        "https://httpstat.us/429",  # simulates rate limiting
        "https://httpstat.us/403",  # simulates blocking
    ]

    for url in bad_urls:
        result = scraper.fetch_page(url)
        status = "Handled gracefully (returned None)" if result is None else "Got content"
        print(f"  {url[-40:]}: {status}")


def test_malformed_html():
    """Test cleaner handles broken HTML."""
    print("\nTest 2: Malformed HTML handling")
    cleaner = ArticleCleaner()

    malformed_cases = [
        "",                          # empty string
        "<p>unclosed paragraph",     # unclosed tag
        "   \n\n\n   ",             # whitespace only
        "<script>alert('xss')</script><p>Real content here that is long enough to pass.</p>",
    ]

    for html in malformed_cases:
        try:
            result = cleaner.clean_html(html)
            print(f"Handled: '{html[:30]}...' → '{result[:40]}'")
        except Exception as e:
            print(f"Failed on: '{html[:30]}' → {e}")


def test_pipeline_monitor():
    """Test pipeline health monitoring."""
    print("\nTest 3: Pipeline health monitor")
    SessionLocal = get_session_factory()
    db = SessionLocal()

    monitor = ScraperMonitor()
    summary = monitor.get_pipeline_summary(db)
    source_stats = monitor.get_source_stats(db)

    print(f"Pipeline summary: {summary}")
    print(f"Source stats:")
    for stat in source_stats:
        print(
            f"{stat['source_name']}: "
            f"{stat['total_articles']} articles, "
            f"status={stat['status']}"
        )

    db.close()


def test_duplicate_stress():
    """Run scraper twice and verify zero duplicates saved."""
    print("\nTest 4: Duplicate stress test")
    from scrapers.sources.the_hindu import TheHinduScraper
    from scrapers.article_store import save_articles

    SessionLocal = get_session_factory()
    db = SessionLocal()

    scraper = TheHinduScraper()
    urls = scraper.get_article_urls()
    article_urls = [u for u in urls if "/article" in u][:3]

    articles = []
    for url in article_urls:
        article = scraper.scrape_article(url)
        if article:
            articles.append(article)

    # First save
    result1 = save_articles(articles, db)
    # Second save — everything should be duplicate
    result2 = save_articles(articles, db)

    print(f"First run:  {result1}")
    print(f"Second run: {result2}")
    print(
        f"Duplicate detection working: "
        f"{result2['saved'] == 0 and result2['skipped_duplicate'] > 0}"
    )

    db.close()


if __name__ == "__main__":
    print("Running Scraping Pipeline QA Tests\n")
    test_retry_logic()
    test_malformed_html()
    test_pipeline_monitor()
    test_duplicate_stress()
    print("\nQA complete")