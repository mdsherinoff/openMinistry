"""
Scrapes all 140 MLAs from the Kerala Legislature website.
Uses the MLA Hostel column to detect ministers, speaker, opposition leader etc.
Run: python scrapers/mla_scraper.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import re
import logging
import httpx
from bs4 import BeautifulSoup
from database.config import get_session_factory
from database.models.minister import Minister

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def parse_role(hostel_text: str) -> tuple[str, str]:
    """
    Parse the MLA Hostel column text into a role and portfolio.
    Returns (role, portfolio) tuple.
    
    Examples:
    - "Minister for Electricity, Environment & Parliamentary Affairs" 
      → ("Minister", "Electricity, Environment & Parliamentary Affairs")
    - "Chief Minister" → ("Chief Minister", "General Administration...")
    - "Leader of Opposition" → ("Leader of Opposition", "")
    - "Speaker" → ("Speaker", "")
    - "" → ("MLA", "")
    """
    if not hostel_text:
        return ("MLA", "")

    text = hostel_text.strip()

    if "chief minister" in text.lower():
        return ("Chief Minister", text)
    elif "speaker" in text.lower() and "deputy" not in text.lower():
        return ("Speaker", "")
    elif "deputy speaker" in text.lower():
        return ("Deputy Speaker", "")
    elif "leader of opposition" in text.lower():
        return ("Leader of Opposition", "")
    elif "deputy leader" in text.lower():
        return ("Deputy Leader of Opposition", "")
    elif text.lower().startswith("minister for"):
        portfolio = re.sub(r"^[Mm]inister\s+for\s+", "", text)
        # Remove the short abbreviation line e.g. "M (Ele.,Env.& PA)"
        portfolio = re.sub(r"\s*M\s*\([^)]+\)\s*$", "", portfolio).strip()
        return ("Minister", portfolio)
    elif "minister" in text.lower():
        return ("Minister", text)
    else:
        return ("MLA", text)


def scrape_mlas():
    """Scrape all MLAs from Kerala Legislature official website."""
    url = "http://www.niyamasabha.org/codes/members.htm"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print("Fetching MLA list from Kerala Legislature website...")

    try:
        with httpx.Client(headers=headers, timeout=60.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    mlas = []

    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        # Col 0: Name
        name_raw = cols[0].get_text(separator=" ", strip=True)

        # Col 1: Constituency
        constituency_raw = cols[1].get_text(strip=True) if len(cols) > 1 else ""

        # Col 4: MLA Hostel / Role
        hostel_raw = cols[4].get_text(separator=" ", strip=True) if len(cols) > 4 else ""

        # Clean name — remove honorifics
        name = re.sub(
            r"^(Shri|Smt|Dr|Sri|Adv|Prof|Shri\.|Smt\.)\.?\s*",
            "", name_raw, flags=re.IGNORECASE
        ).strip()
        name = re.sub(r"\s+", " ", name).strip()

        # Clean constituency
        constituency = re.sub(r"\s*\(\d+\)\s*$", "", constituency_raw).strip()
        constituency = re.sub(r"\s+", " ", constituency).strip()

        # Skip invalid rows
        if not name or len(name) < 3 or len(name) > 100:
            continue
        if any(char in name for char in ["\n", "\r", "|", "/"]):
            continue
        if any(word in name.lower() for word in [
            "name", "info", "government", "speaker", "minister",
            "member", "business", "library", "click", "district",
            "facilities", "previous", "mailing", "party", "session",
            "constituency", "general", "council", "deputy", "http"
        ]):
            continue
        if re.match(r"^\d+$", name):
            continue
        if not re.search(r"[a-zA-Z]", name):
            continue

        # Parse role from hostel column
        role, portfolio = parse_role(hostel_raw)

        mlas.append({
            "name": name[:255],
            "constituency": constituency[:255],
            "role": role,
            "portfolio": portfolio[:255] if portfolio else f"MLA - {constituency}"[:255],
        })

    # Remove duplicates by name
    seen = set()
    unique_mlas = []
    for mla in mlas:
        if mla["name"] not in seen:
            seen.add(mla["name"])
            unique_mlas.append(mla)

    return unique_mlas


def seed_mlas(mlas: list):
    """Save MLAs to the ministers table."""
    SessionLocal = get_session_factory()
    db = SessionLocal()

    added = 0
    skipped = 0

    # Print role summary first
    roles = {}
    for mla in mlas:
        role = mla["role"]
        roles[role] = roles.get(role, 0) + 1

    print("\nRole breakdown:")
    for role, count in sorted(roles.items()):
        print(f"  {role}: {count}")
    print()

    for mla in mlas:
        existing = db.query(Minister).filter(
            Minister.name == mla["name"]
        ).first()

        if existing:
            # Update role if we have better info
            if mla["role"] != "MLA" and existing.portfolio.startswith("MLA"):
                existing.portfolio = mla["portfolio"]
                db.commit()
                print(f"Updated role: {mla['name']} → {mla['role']}")
            skipped += 1
            continue

        minister = Minister(
            name=mla["name"],
            portfolio=mla["portfolio"],
            constituency=mla["constituency"],
            is_active=1,
            bio=f"{mla['role']} — {mla['constituency']}",
        )
        db.add(minister)
        db.commit()

        icon = "⭐" if mla["role"] != "MLA" else " "
        print(f"{icon} {mla['role']}: {mla['name']} ({mla['constituency']})")
        added += 1

    db.close()
    print(f"\nDone. Added {added}, skipped {skipped}.")


if __name__ == "__main__":
    # Clear old data first
    print("Clearing old MLA data...")
    SessionLocal = get_session_factory()
    db = SessionLocal()
    from database.models.statement import Statement
    from database.models.moderation_log import ModerationLog
    # Must delete in order: logs → statements → ministers
    db.query(ModerationLog).delete()
    db.query(Statement).delete()
    db.query(Minister).delete()
    db.commit()
    db.close()
    print("Cleared.\n")

    mlas = scrape_mlas()
    print(f"Found {len(mlas)} MLAs\n")

    if mlas:
        seed_mlas(mlas)