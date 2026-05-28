import re
import logging
from sqlalchemy.orm import Session
from database.models.minister import Minister

logger = logging.getLogger(__name__)


class NameDetector:
    """
    Detects mentions of Kerala ministers and MLAs in article text.
    Uses multiple strategies:
    1. Direct name matching
    2. Alias matching
    3. Portfolio/title matching
    4. Partial name matching
    """

    def __init__(self):
        self.ministers = []
        self.name_index = {}      # lowercase name -> minister
        self.alias_index = {}     # lowercase alias -> minister
        self.portfolio_index = {} # lowercase portfolio keyword -> minister

    def load_ministers(self, db: Session):
        """Load all ministers from the database into memory."""
        self.ministers = db.query(Minister).filter(
            Minister.is_active == 1
        ).all()

        self.name_index = {}
        self.alias_index = {}
        self.portfolio_index = {}

        for minister in self.ministers:
            # Index by full name
            self.name_index[minister.name.lower()] = minister

            # Index by name parts (first name, last name)
            parts = minister.name.split()
            for part in parts:
                if len(part) > 3:  # skip initials like "K." or "V."
                    key = part.lower()
                    if key not in self.name_index:
                        self.name_index[key] = minister

            # Index by Malayalam name
            if minister.name_malayalam:
                self.name_index[minister.name_malayalam.lower()] = minister

            # Index by aliases stored in bio
            if minister.bio and "ALIASES:" in minister.bio:
                alias_section = minister.bio.split("ALIASES:")[-1]
                aliases = [a.strip() for a in alias_section.split(",")]
                for alias in aliases:
                    if alias:
                        self.alias_index[alias.lower()] = minister

            # Index by portfolio keywords
            if minister.portfolio:
                # Extract key portfolio words
                portfolio_words = re.findall(
                    r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
                    minister.portfolio
                )
                for word in portfolio_words:
                    if len(word) > 5:
                        self.portfolio_index[word.lower()] = minister

        logger.info(
            f"Loaded {len(self.ministers)} ministers, "
            f"{len(self.name_index)} name entries, "
            f"{len(self.alias_index)} aliases"
        )

    def detect_mentions(self, text: str) -> list[dict]:
        """
        Find all minister mentions in a text.
        Returns list of dicts with minister and context.
        """
        if not text or not self.ministers:
            return []

        mentions = []
        seen_ministers = set()  # avoid duplicate mentions

        # Strategy 1 — Full name matching
        for name_lower, minister in self.name_index.items():
            if len(name_lower) < 4:
                continue
            pattern = re.compile(
                r'\b' + re.escape(name_lower) + r'\b',
                re.IGNORECASE
            )
            for match in pattern.finditer(text):
                if minister.id not in seen_ministers:
                    context = self._extract_context(text, match.start(), match.end())
                    mentions.append({
                        "minister_id": minister.id,
                        "minister_name": minister.name,
                        "matched_text": match.group(),
                        "match_type": "name",
                        "context": context,
                        "position": match.start(),
                    })
                    seen_ministers.add(minister.id)

        # Strategy 2 — Alias matching
        for alias_lower, minister in self.alias_index.items():
            if minister.id in seen_ministers:
                continue
            if len(alias_lower) < 4:
                continue
            pattern = re.compile(
                r'\b' + re.escape(alias_lower) + r'\b',
                re.IGNORECASE
            )
            for match in pattern.finditer(text):
                if minister.id not in seen_ministers:
                    context = self._extract_context(text, match.start(), match.end())
                    mentions.append({
                        "minister_id": minister.id,
                        "minister_name": minister.name,
                        "matched_text": match.group(),
                        "match_type": "alias",
                        "context": context,
                        "position": match.start(),
                    })
                    seen_ministers.add(minister.id)

        # Strategy 3 — Title matching
        # e.g. "Health Minister", "the CM", "Chief Minister"
        title_patterns = [
            (r'\bChief\s+Minister\b', "Chief Minister"),
            (r'\bCM\b', "Chief Minister"),
            (r'\bHealth\s+Minister\b', "Health"),
            (r'\bFinance\s+Minister\b', "Finance"),
            (r'\bHome\s+Minister\b', "Home"),
            (r'\bEducation\s+Minister\b', "Education"),
            (r'\bTransport\s+Minister\b', "Transport"),
            (r'\bAgriculture\s+Minister\b', "Agriculture"),
            (r'\bForest\s+Minister\b', "Forest"),
            (r'\bRevenue\s+Minister\b', "Revenue"),
            (r'\bPWD\s+Minister\b', "Public Works"),
            (r'\bTourism\s+Minister\b', "Tourism"),
            (r'\bOpposition\s+Leader\b', "Leader of Opposition"),
            (r'\bLeader\s+of\s+Opposition\b', "Leader of Opposition"),
            (r'\bSpeaker\b', "Speaker"),
        ]

        for pattern_str, portfolio_key in title_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            for match in pattern.finditer(text):
                # Find minister with this portfolio
                minister = self._find_by_portfolio(portfolio_key)
                if minister and minister.id not in seen_ministers:
                    context = self._extract_context(
                        text, match.start(), match.end()
                    )
                    mentions.append({
                        "minister_id": minister.id,
                        "minister_name": minister.name,
                        "matched_text": match.group(),
                        "match_type": "title",
                        "context": context,
                        "position": match.start(),
                    })
                    seen_ministers.add(minister.id)

        # Sort by position in text
        mentions.sort(key=lambda x: x["position"])
        return mentions

    def _find_by_portfolio(self, keyword: str) -> Minister | None:
        """Find a minister by portfolio keyword."""
        keyword_lower = keyword.lower()

        # Special cases
        if keyword_lower in ("chief minister", "cm"):
            for m in self.ministers:
                if m.bio and "Chief Minister" in m.bio:
                    return m

        if keyword_lower == "leader of opposition":
            for m in self.ministers:
                if m.bio and "Leader of Opposition" in m.bio:
                    return m

        if keyword_lower == "speaker":
            for m in self.ministers:
                if m.bio and m.bio.startswith("Speaker"):
                    return m

        # Search by portfolio field
        for minister in self.ministers:
            if minister.portfolio and keyword_lower in minister.portfolio.lower():
                return minister

        return None

    def _extract_context(
        self, text: str, start: int, end: int, window: int = 200
    ) -> str:
        """Extract surrounding context around a match."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        context = text[ctx_start:ctx_end].strip()
        # Clean up whitespace
        context = re.sub(r"\s+", " ", context)
        return context

    def get_detection_summary(self, mentions: list[dict]) -> dict:
        """Summarize detection results."""
        if not mentions:
            return {"total": 0, "ministers": []}

        minister_counts = {}
        for mention in mentions:
            name = mention["minister_name"]
            minister_counts[name] = minister_counts.get(name, 0) + 1

        return {
            "total": len(mentions),
            "unique_ministers": len(minister_counts),
            "ministers": [
                {"name": name, "mentions": count}
                for name, count in sorted(
                    minister_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ],
        }