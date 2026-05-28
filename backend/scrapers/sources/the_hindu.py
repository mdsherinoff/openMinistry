import logging
from datetime import datetime, timezone
from scrapers.base_scraper import BaseScraper
from scrapers.source_config import SOURCE_CONFIGS

logger = logging.getLogger(__name__)


class TheHinduScraper(BaseScraper):
    """Scraper for The Hindu - Kerala section."""

    def __init__(self):
        super().__init__(SOURCE_CONFIGS["thehindu.com"])

    def get_article_urls(self) -> list[str]:
        """Crawl the Kerala section and collect article URLs."""
        urls = set()

        for list_url in self.config["article_list_urls"]:
            html = self.fetch_page(list_url)
            if not html:
                logger.warning(f"Could not fetch listing page: {list_url}")
                continue

            soup = self.parse_html(html)
            selector = self.selectors["article_links"]

            for link in soup.select(selector):
                href = link.get("href", "")
                if not href:
                    continue
                # Make absolute URL
                if href.startswith("/"):
                    href = f"https://www.thehindu.com{href}"
                # Filter to only Kerala articles
                if "/kerala/" in href and href.startswith("http") and "/article" in href:
                    urls.add(href.split("?")[0])

        return list(urls)

    def scrape_article(self, url: str) -> dict | None:
        """Scrape a single article from The Hindu."""
        html = self.fetch_page(url)
        if not html:
            return None

        soup = self.parse_html(html)

        title = self.extract_text(soup, self.selectors["title"])
        if not title:
            logger.debug(f"No title found for {url}")
            return None

        content = self.clean_content(soup, self.selectors["content"])
        if not content or len(content) < 100:
            logger.debug(f"No content found for {url}")
            return None

        author = self.extract_text(soup, self.selectors["author"])
        published_at = self.extract_date(soup, self.selectors["date"])

        return {
            "url": url,
            "url_hash": self.make_url_hash(url),
            "title": title,
            "author": author,
            "published_at": published_at,
            "raw_content": content,
            "cleaned_content": content,
            "language": "en",
            "source_name": self.name,
            "scraped_at": datetime.now(timezone.utc),
        }