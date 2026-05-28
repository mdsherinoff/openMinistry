"""
Populates the sources table from SOURCE_CONFIGS.
Run once: python scrapers/seed_sources.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database.config import get_session_factory
from database.models.source import Source
from scrapers.source_config import SOURCE_CONFIGS


def seed_sources():
    SessionLocal = get_session_factory()
    db = SessionLocal()

    for domain, config in SOURCE_CONFIGS.items():
        existing = db.query(Source).filter(
            Source.website == config["base_url"]
        ).first()

        if existing:
            print(f"⏭Already exists: {config['name']}")
            continue

        source = Source(
            name=config["name"],
            website=config["base_url"],
            language=config["language"],
            credibility_score=config["credibility_score"],
            scrape_frequency_minutes=config["scrape_frequency_minutes"],
            is_active=1,
        )
        db.add(source)
        print(f"Added source: {config['name']}")

    db.commit()
    db.close()
    print("\nDone. Sources are ready.")


if __name__ == "__main__":
    seed_sources()