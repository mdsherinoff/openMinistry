"""
Test Malayalam scrapers.
Usage: python scrapers/test_malayalam_scrapers.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

from scrapers.sources.mathrubhumi import MathrubhumiScraper
from scrapers.sources.manorama import ManoramaScraper
from scrapers.article_store import save_articles
from database.config import get_session_factory


def test_scraper(scraper, name):
    print(f"\n{'='*50}")
    print(f"Testing {name} scraper")
    print('='*50)

    # Get URLs
    print("Step 1: Fetching article URLs...")
    urls = scraper.get_article_urls()
    print(f"Found {len(urls)} URLs")

    if not urls:
        print(f"No URLs found for {name}")
        return

    # Show sample URLs
    print("Sample URLs:")
    for url in urls[:3]:
        print(f"  - {url}")

    # Scrape first article
    print("\nStep 2: Scraping first article...")
    article = scraper.scrape_article(urls[0])

    if article:
        print(f"Title: {article['title'][:80]}")
        print(f"Language: {article['language']}")
        print(f"Author: {article['author']}")
        print(f"Content length: {len(article['raw_content'])} chars")
        print(f"Preview: {article['raw_content'][:200]}...")
    else:
        print(f"Could not scrape article — selectors may need updating")
        # Try next URLs
        print("Trying next 3 URLs...")
        for url in urls[1:4]:
            article = scraper.scrape_article(url)
            if article:
                print(f"Success with: {url}")
                print(f"Title: {article['title'][:80]}")
                break
        else:
            print("All attempts failed — check selectors")
            return

    # Save to database
    if article:
        print("\nStep 3: Saving to database...")
        SessionLocal = get_session_factory()
        db = SessionLocal()
        result = save_articles([article], db)
        db.close()
        print(f"Result: {result}")


def main():
    print("Testing Malayalam Scrapers\n")

    test_scraper(MathrubhumiScraper(), "Mathrubhumi")
    test_scraper(ManoramaScraper(), "Manorama Online")

    print("\nTesting complete")


if __name__ == "__main__":
    main()