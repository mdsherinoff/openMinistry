"""
Test the scraper manually before hooking it into Celery.
Usage: python scrapers/test_scraper.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

from scrapers.sources.the_hindu import TheHinduScraper
from scrapers.article_store import save_articles
from database.config import get_session_factory


def test():
    print("Testing The Hindu scraper...\n")

    scraper = TheHinduScraper()

    # Step 1: Get article URLs
    print("Step 1: Fetching article URLs...")
    urls = scraper.get_article_urls()
    print(f"Found {len(urls)} URLs")
    if urls:
        print("Sample URLs:")
        for url in urls[:3]:
            print(f"  - {url}")

    if not urls:
        print("No URLs found. Check selectors.")
        return

    # Step 2: Scrape first article
    print("\nStep 2: Scraping first article...")

    # Filter out listing pages
    article_urls = [u for u in urls if "/article" in u]
    print(f"Article URLs (filtered): {len(article_urls)}")

    if not article_urls:
        print("No article URLs after filtering.")
        return

    print(f"Trying: {article_urls[0]}")
    article = scraper.scrape_article(article_urls[0])

    if article:
        print(f"Title: {article['title']}")
        print(f"Author: {article['author']}")
        print(f"Date: {article['published_at']}")
        print(f"Content length: {len(article['raw_content'])} chars")
        print(f"Content preview: {article['raw_content'][:200]}...")
    else:
        # Debug what the page actually contains
        print("Could not scrape article. Debugging selectors...")
        html = scraper.fetch_page(article_urls[0])
        if html:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            print(f"Page title tag: {soup.title.string if soup.title else 'None'}")
            print(f"H1 tags found: {[h.get_text()[:50] for h in soup.find_all('h1')[:3]]}")
            divs = soup.find_all("div", class_=True)
            print(f"First 10 div classes: {[' '.join(d.get('class', [])) for d in divs[:10]]}")
        return

    # Step 3: Save to database
    print("\nStep 3: Saving to database...")
    SessionLocal = get_session_factory()
    db = SessionLocal()
    result = save_articles([article], db)
    db.close()
    print(f"Result: {result}")


if __name__ == "__main__":
    test()