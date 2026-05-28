import re
import logging
import unicodedata
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ArticleCleaner:
    """
    Cleans raw scraped article content.
    Removes noise, normalizes text, and prepares
    content for statement extraction.
    """

    # Phrases that indicate junk content
    JUNK_PHRASES = [
        "subscribe to continue reading",
        "subscribe now",
        "sign in to read",
        "create a free account",
        "already a subscriber",
        "get unlimited access",
        "read more stories",
        "also read",
        "you may also like",
        "related stories",
        "advertisement",
        "click here to",
        "follow us on",
        "share this article",
        "print this article",
        "comments section",
        "leave a comment",
        "newsletter",
        "download the app",
        "watch live",
        "live updates",
        # Malayalam junk phrases
        "വായിക്കുക",
        "കൂടുതൽ വാർത്തകൾ",
        "ഇതും വായിക്കുക",
        "പ്രതികരണം രേഖപ്പെടുത്തുക",
        "ഷെയർ ചെയ്യുക",
        "ഡൗൺലോഡ് ചെയ്യുക",
        "സബ്സ്ക്രൈബ് ചെയ്യുക",
    ]

    # Tags to completely remove
    REMOVE_TAGS = [
        "script", "style", "nav", "footer", "header",
        "aside", "form", "iframe", "noscript", "figure",
        "figcaption", "button", "input", "select",
        "advertisement", "ad", "svg", "canvas",
    ]

    # CSS classes/ids that indicate junk
    JUNK_CLASSES = [
        "ad", "advertisement", "banner", "sidebar",
        "related", "recommended", "newsletter", "subscribe",
        "social", "share", "comment", "popup", "modal",
        "cookie", "paywall", "subscription", "promo",
        "widget", "footer", "header", "navigation", "nav",
        "breadcrumb", "tag", "label", "caption",
    ]

    def clean_html(self, html: str) -> str:
        """
        Full cleaning pipeline for raw HTML content.
        Returns clean plain text.
        """
        if not html:
            return ""

        soup = BeautifulSoup(html, "lxml")

        # Step 1 — Remove unwanted tags entirely
        self._remove_tags(soup)

        # Step 2 — Remove junk by class/id
        self._remove_junk_elements(soup)

        # Step 3 — Extract paragraphs
        text = self._extract_paragraphs(soup)

        # Step 4 — Normalize unicode
        text = self._normalize_unicode(text)

        # Step 5 — Clean whitespace
        text = self._clean_whitespace(text)

        # Step 6 — Remove junk lines
        text = self._remove_junk_lines(text)

        return text.strip()

    def clean_text(self, text: str) -> str:
        """
        Clean already-extracted plain text
        (no HTML parsing needed).
        """
        if not text:
            return ""
        text = self._normalize_unicode(text)
        text = self._clean_whitespace(text)
        text = self._remove_junk_lines(text)
        return text.strip()

    def _remove_tags(self, soup: BeautifulSoup) -> None:
        """Remove unwanted HTML tags completely."""
        for tag in self.REMOVE_TAGS:
            for element in soup.find_all(tag):
                element.decompose()

    def _remove_junk_elements(self, soup: BeautifulSoup) -> None:
        """Remove elements with junk classes or IDs."""
        for element in soup.find_all(True):
            classes = " ".join(element.get("class", [])).lower()
            element_id = element.get("id", "").lower()
            combined = f"{classes} {element_id}"

            if any(junk in combined for junk in self.JUNK_CLASSES):
                element.decompose()

    def _extract_paragraphs(self, soup: BeautifulSoup) -> str:
        """Extract paragraph text preserving structure."""
        paragraphs = []

        for p in soup.find_all("p"):
            text = p.get_text(separator=" ", strip=True)
            if text and len(text) > 30:  # skip very short fragments
                paragraphs.append(text)

        if paragraphs:
            return "\n\n".join(paragraphs)

        # Fallback — get all text if no paragraphs found
        return soup.get_text(separator="\n", strip=True)

    def _normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters."""
        # Normalize to NFC form (important for Malayalam)
        text = unicodedata.normalize("NFC", text)

        # Replace common unicode quotes with standard ones
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        text = text.replace("\u00a0", " ")  # non-breaking space
        text = text.replace("\u200b", "")   # zero-width space

        return text

    def _clean_whitespace(self, text: str) -> str:
        """Normalize whitespace throughout the text."""
        # Replace multiple spaces with single space
        text = re.sub(r" {2,}", " ", text)

        # Replace more than 2 newlines with exactly 2
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Clean up space around newlines
        text = re.sub(r" *\n *", "\n", text)

        return text

    def _remove_junk_lines(self, text: str) -> str:
        """Remove lines that contain junk phrases."""
        lines = text.split("\n")
        clean_lines = []

        for line in lines:
            line_lower = line.lower().strip()

            # Skip empty lines between paragraphs (keep structure)
            if not line_lower:
                clean_lines.append("")
                continue

            # Skip very short lines (likely nav items or labels)
            if len(line_lower) < 15:
                continue

            # Skip lines with junk phrases
            if any(phrase in line_lower for phrase in self.JUNK_PHRASES):
                continue

            clean_lines.append(line)

        return "\n".join(clean_lines)

    def is_content_sufficient(self, text: str) -> bool:
        """
        Check if cleaned content is long enough
        to be worth storing and processing.
        """
        if not text:
            return False
        words = len(text.split())
        return words >= 50  # minimum 50 words

    def extract_first_paragraph(self, text: str) -> str:
        """Get just the first paragraph — useful for previews."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return paragraphs[0] if paragraphs else text[:300]