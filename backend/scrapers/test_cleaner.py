"""
Test the article cleaner.
Usage: python scrapers/test_cleaner.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

from scrapers.cleaner import ArticleCleaner
from scrapers.cleaning_service import clean_pending_articles
from database.config import get_session_factory
from database.models.article import Article


def test():
    print("Testing Article Cleaner\n")
    cleaner = ArticleCleaner()

    # Test 1 — Clean a sample HTML snippet
    print("Test 1: Clean sample HTML")
    sample_html = """
    <div class="article-body">
        <p>Kerala Chief Minister Pinarayi Vijayan said that the government
        would strengthen public hospitals across the state.</p>
        <p>He was speaking at a press conference in Thiruvananthapuram.</p>
        <div class="advertisement">Buy now! Click here!</div>
        <p>The minister added that a budget of 500 crore rupees had been
        allocated for the health sector this year.</p>
        <p>Subscribe to continue reading this article.</p>
        <p>Follow us on social media for more updates.</p>
    </div>
    """
    cleaned = cleaner.clean_html(sample_html)
    print(f"Cleaned text:\n{cleaned}")
    print(f"Sufficient content: {cleaner.is_content_sufficient(cleaned)}\n")

    # Test 2 — Clean articles already in the database
    print("Test 2: Clean articles in database")
    SessionLocal = get_session_factory()
    db = SessionLocal()

    total = db.query(Article).count()
    print(f"Total articles in DB: {total}")

    result = clean_pending_articles(db)
    print(f"Result: {result}")

    # Show a cleaned article
    cleaned_article = db.query(Article).filter(
        Article.scrape_status == "cleaned"
    ).first()

    if cleaned_article:
        print(f"\nSample cleaned article:")
        print(f"Title: {cleaned_article.title}")
        print(f"Status: {cleaned_article.scrape_status}")
        print(f"Preview: {cleaned_article.cleaned_content[:300]}...")

    db.close()


if __name__ == "__main__":
    test()