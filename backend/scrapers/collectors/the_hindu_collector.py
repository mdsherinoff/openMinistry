import logging
import re
from bs4 import BeautifulSoup
from scrapers.url_collector import BaseURLCollector
from scrapers.source_config import SOURCE_CONFIGS

logger = logging.getLogger(__name__)


class TheHinduCollector(BaseURLCollector):
    """Collects article URLs from The Hindu Kerala section."""

    def __init__(self):
        super().__init__(SOURCE_CONFIGS["thehindu.com"])

    def get_article_urls(self) -> list[dict]:
        urls = []
        seen = set()

        for list_url in self.config["article_list_urls"]:
            html = self.fetch_page(list_url)
            if not html:
                logger.warning(f"Could not fetch: {list_url}")
                continue

            soup = BeautifulSoup(html, "lxml")

            for a in soup.find_all("a", href=True):
                href = a["href"]

                # Make absolute
                if href.startswith("/"):
                    href = f"https://www.thehindu.com{href}"

                # Filter to Kerala articles only
                if "/kerala/" not in href:
                    continue
                if "/article" not in href:
                    continue
                if not href.startswith("http"):
                    continue

                url = href.split("?")[0]
                if url in seen:
                    continue
                seen.add(url)

                # Extract title from link text
                title = a.get_text(strip=True)
                if not title or len(title) < 10:
                    # Try parent element
                    parent = a.find_parent(
                        ["h2", "h3", "h4", "div", "li"]
                    )
                    if parent:
                        title = parent.get_text(strip=True)[:300]

                urls.append({
                    "url": url,
                    "title": title[:500] if title else None,
                    "published_at": None,
                })

        logger.info(f"TheHindu: found {len(urls)} article URLs")
        return urls