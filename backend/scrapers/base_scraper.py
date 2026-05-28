import hashlib
import logging
import httpx
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Base class for all scrapers.
    Every news source scraper inherits from this.
    """

    def __init__(self, source_config: dict):
        self.config = source_config
        self.name = source_config["name"]
        self.base_url = source_config["base_url"]
        self.selectors = source_config["selectors"]
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,ml;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def make_url_hash(self, url: str) -> str:
        """Create a unique hash for a URL — used for deduplication."""
        return hashlib.sha256(url.strip().encode()).hexdigest()

    def fetch_page(self, url: str) -> str | None:
        """Fetch a page and return its HTML content."""
        try:
            with httpx.Client(
                headers=self.headers,
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML into a BeautifulSoup object."""
        return BeautifulSoup(html, "lxml")

    def extract_text(self, soup: BeautifulSoup, selector: str) -> str | None:
        """Try multiple CSS selectors and return the first match."""
        for sel in selector.split(","):
            sel = sel.strip()
            element = soup.select_one(sel)
            if element:
                return element.get_text(strip=True)
        return None

    def clean_content(self, soup: BeautifulSoup, selector: str) -> str | None:
        """Extract and clean article body content."""
        for sel in selector.split(","):
            sel = sel.strip()
            element = soup.select_one(sel)
            if element:
                # Remove unwanted tags
                for tag in element.find_all(
                    ["script", "style", "nav", "footer",
                     "aside", "form", "iframe", "ad"]
                ):
                    tag.decompose()
                # Get clean text with paragraph breaks
                paragraphs = element.find_all("p")
                if paragraphs:
                    return "\n\n".join(
                        p.get_text(strip=True)
                        for p in paragraphs
                        if p.get_text(strip=True)
                    )
                return element.get_text(separator="\n", strip=True)
        return None

    def extract_date(self, soup: BeautifulSoup, selector: str) -> datetime | None:
        """Extract and parse article publish date."""
        for sel in selector.split(","):
            sel = sel.strip()
            element = soup.select_one(sel)
            if element:
                # Try datetime attribute first
                dt = element.get("datetime")
                if dt:
                    try:
                        return datetime.fromisoformat(
                            dt.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass
                # Fall back to text content
                text = element.get_text(strip=True)
                if text:
                    try:
                        return datetime.fromisoformat(text)
                    except ValueError:
                        pass
        return datetime.now(timezone.utc)

    @abstractmethod
    def get_article_urls(self) -> list[str]:
        """Fetch list of article URLs from the source homepage."""
        pass

    @abstractmethod
    def scrape_article(self, url: str) -> dict | None:
        """Scrape a single article and return structured data."""
        pass

    def scrape_all(self) -> list[dict]:
        """Main entry point — scrape all articles from this source."""
        from scrapers.cleaner import ArticleCleaner
        cleaner = ArticleCleaner()

        logger.info(f"Starting scrape: {self.name}")
        urls = self.get_article_urls()
        logger.info(f"Found {len(urls)} article URLs from {self.name}")

        articles = []
        for url in urls[:20]:
            article = self.scrape_article(url)
            if article:
                # Clean content immediately after scraping
                if article.get("raw_content"):
                    article["cleaned_content"] = cleaner.clean_text(
                        article["raw_content"]
                    )
                articles.append(article)

        logger.info(
            f"Successfully scraped {len(articles)} articles from {self.name}"
        )
        return articles