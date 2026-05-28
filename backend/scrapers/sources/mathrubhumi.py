import logging
from datetime import datetime, timezone
from scrapers.base_scraper import BaseScraper
from scrapers.source_config import SOURCE_CONFIGS

logger = logging.getLogger(__name__)


class MathrubhumiScraper(BaseScraper):
    """Scraper for Mathrubhumi newspaper."""

    def __init__(self):
        super().__init__(SOURCE_CONFIGS["mathrubhumi.com"])

    def get_article_urls(self) -> list[str]:
        """Crawl Mathrubhumi Kerala section for article URLs."""
        urls = set()

        for list_url in self.config["article_list_urls"]:
            html = self.fetch_page(list_url)
            if not html:
                logger.warning(f"Could not fetch: {list_url}")
                continue

            soup = self.parse_html(html)

            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                if not href:
                    continue

                # Make absolute URL
                if href.startswith("/"):
                    href = f"https://www.mathrubhumi.com{href}"

                # Filter to news articles only
                if (
                    "mathrubhumi.com" in href
                    and "/news/" in href
                    and href.startswith("http")
                    and len(href) > 50
                ):
                    urls.add(href.split("?")[0])

        logger.info(f"Mathrubhumi: found {len(urls)} URLs")
        return list(urls)

    def scrape_article(self, url: str) -> dict | None:
        """Scrape a single Mathrubhumi article."""
        html = self.fetch_page(url)
        if not html:
            return None

        soup = self.parse_html(html)

        # Try multiple title selectors
        title = (
            self.extract_text(soup, "h1.article-title")
            or self.extract_text(soup, "h1.title")
            or self.extract_text(soup, "h1")
        )

        if not title:
            logger.debug(f"No title found: {url}")
            return None

        # Try multiple content selectors
        content = (
            self.clean_content(soup, "div.article-body")
            or self.clean_content(soup, "div.story-content")
            or self.clean_content(soup, "div.content-area")
            or self.clean_content(soup, "article")
        )

        if not content or len(content) < 100:
            logger.debug(f"No content found: {url}")
            return None

        author = (
            self.extract_text(soup, "span.author-name")
            or self.extract_text(soup, "div.author")
            or self.extract_text(soup, "span.reporter-name")
            or "Mathrubhumi Bureau"
        )

        published_at = self.extract_date(
            soup,
            "time[datetime], span.date, div.article-date"
        )

        return {
            "url": url,
            "url_hash": self.make_url_hash(url),
            "title": title,
            "author": author,
            "published_at": published_at,
            "raw_content": content,
            "cleaned_content": content,
            "language": "ml",
            "source_name": self.name,
            "scraped_at": datetime.now(timezone.utc),
        }