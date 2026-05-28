import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractedQuote:
    text: str
    quote_type: str        # "direct" | "indirect" | "reported"
    confidence: float      # 0.0 to 1.0
    minister_name: str
    context: str


class QuoteExtractor:
    """
    Extracts quotes and statements attributed to ministers.

    Three types:
    1. Direct quotes   — "We will build 1000 hospitals," he said.
    2. Indirect quotes — The minister said that they would build hospitals.
    3. Reported speech — The CM announced a new housing scheme.
    """

    # Verbs that introduce direct/indirect speech
    SPEECH_VERBS = [
        "said", "stated", "announced", "declared", "told",
        "mentioned", "added", "noted", "explained", "claimed",
        "argued", "asserted", "confirmed", "revealed", "admitted",
        "denied", "stressed", "emphasised", "emphasized", "warned",
        "urged", "called", "demanded", "promised", "pledged",
        "informed", "clarified", "pointed out", "highlighted",
        "indicated", "suggested", "proposed", "directed",
        "instructed", "expressed", "commented", "remarked",
        "observed", "recalled", "acknowledged", "maintained",
    ]

    # Patterns for direct quotes (text in quotes)
    DIRECT_QUOTE_PATTERNS = [
        # "quote text," minister said
        r'"([^"]{20,500})"[,.]?\s*(?:the\s+)?(?:minister|CM|chief minister|'
        r'he|she|they)?\s*(?:' + '|'.join(SPEECH_VERBS) + r')',

        # minister said, "quote text"
        r'(?:' + '|'.join(SPEECH_VERBS) + r')[,.]?\s*"([^"]{20,500})"',

        # 'quote text,' minister said (single quotes)
        r"'([^']{20,500})'[,.]?\s*(?:the\s+)?(?:minister|CM)?\s*"
        r'(?:' + '|'.join(SPEECH_VERBS) + r')',
    ]

    # Patterns for indirect speech
    INDIRECT_PATTERNS = [
        # minister said that...
        r'(?:minister|CM|chief minister|he|she|they)\s+'
        r'(?:' + '|'.join(SPEECH_VERBS) + r')\s+that\s+([^.!?]{20,400}[.!?])',

        # According to minister...
        r'[Aa]ccording\s+to\s+(?:the\s+)?(?:minister|CM|chief minister)'
        r'[,.]?\s+([^.!?]{20,400}[.!?])',

        # minister verb + object (reported speech)
        r'(?:The\s+)?(?:minister|CM|chief minister)\s+'
        r'(?:' + '|'.join(SPEECH_VERBS) + r')\s+([^.!?]{20,400}[.!?])',
    ]

    def extract_quotes(
        self,
        text: str,
        minister_name: str,
        minister_context: str = "",
    ) -> list[ExtractedQuote]:
        """
        Extract all quotes attributed to a minister from text.
        """
        quotes = []

        if not text:
            return quotes

        # Step 1 — Extract direct quotes
        direct = self._extract_direct_quotes(text, minister_name)
        quotes.extend(direct)

        # Step 2 — Extract indirect quotes
        indirect = self._extract_indirect_quotes(text, minister_name)
        quotes.extend(indirect)

        # Step 3 — Extract from minister's context window
        if minister_context:
            context_quotes = self._extract_from_context(
                minister_context, minister_name
            )
            quotes.extend(context_quotes)

        # Deduplicate by text similarity
        quotes = self._deduplicate(quotes)

        # Sort by confidence
        quotes.sort(key=lambda q: q.confidence, reverse=True)

        return quotes

    def _extract_direct_quotes(
        self, text: str, minister_name: str
    ) -> list[ExtractedQuote]:
        """Extract text in quotation marks near minister mentions."""
        quotes = []

        # Find all quoted text in the document
        quote_pattern = re.compile(r'"([^"]{20,500})"', re.DOTALL)

        for match in quote_pattern.finditer(text):
            quote_text = match.group(1).strip()
            quote_text = re.sub(r"\s+", " ", quote_text)

            # Check if minister is mentioned near this quote (±300 chars)
            start = max(0, match.start() - 300)
            end = min(len(text), match.end() + 300)
            surrounding = text[start:end].lower()

            minister_last_name = minister_name.split()[-1].lower()
            minister_first_name = minister_name.split()[0].lower()

            is_attributed = (
                minister_last_name in surrounding
                or minister_first_name in surrounding
                or any(verb in surrounding for verb in self.SPEECH_VERBS)
            )

            if is_attributed and len(quote_text) >= 20:
                quotes.append(ExtractedQuote(
                    text=quote_text,
                    quote_type="direct",
                    confidence=0.85,
                    minister_name=minister_name,
                    context=surrounding[:200],
                ))

        return quotes

    def _extract_indirect_quotes(
        self, text: str, minister_name: str
    ) -> list[ExtractedQuote]:
        """Extract indirect speech attributed to minister."""
        quotes = []

        # Split into sentences
        sentences = self._split_sentences(text)

        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            minister_last = minister_name.split()[-1].lower()

            # Check if this sentence mentions the minister
            # and contains a speech verb
            has_minister = (
                minister_last in sentence_lower
                or minister_name.lower() in sentence_lower
            )
            has_speech_verb = any(
                verb in sentence_lower for verb in self.SPEECH_VERBS
            )

            if has_minister and has_speech_verb:
                # Clean up the sentence
                clean = sentence.strip()
                clean = re.sub(r"\s+", " ", clean)

                if len(clean) >= 30:
                    # Get context from surrounding sentences
                    ctx_start = max(0, i - 1)
                    ctx_end = min(len(sentences), i + 2)
                    context = " ".join(sentences[ctx_start:ctx_end])

                    quotes.append(ExtractedQuote(
                        text=clean,
                        quote_type="indirect",
                        confidence=0.65,
                        minister_name=minister_name,
                        context=context[:300],
                    ))

        return quotes

    def _extract_from_context(
        self, context: str, minister_name: str
    ) -> list[ExtractedQuote]:
        """
        Extract statements from the context window around
        a minister mention.
        """
        quotes = []
        sentences = self._split_sentences(context)

        for sentence in sentences:
            sentence = sentence.strip()
            sentence_lower = sentence.lower()

            has_speech_verb = any(
                verb in sentence_lower for verb in self.SPEECH_VERBS
            )

            if has_speech_verb and len(sentence) >= 40:
                quotes.append(ExtractedQuote(
                    text=re.sub(r"\s+", " ", sentence),
                    quote_type="reported",
                    confidence=0.50,
                    minister_name=minister_name,
                    context=context[:200],
                ))

        return quotes

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Split on sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter out very short fragments
        return [s for s in sentences if len(s.strip()) > 15]

    def _deduplicate(
        self, quotes: list[ExtractedQuote]
    ) -> list[ExtractedQuote]:
        """Remove duplicate or near-duplicate quotes."""
        if not quotes:
            return quotes

        unique = []
        seen_texts = []

        for quote in quotes:
            # Check if very similar to existing quote
            is_duplicate = False
            for seen in seen_texts:
                # Simple overlap check
                shorter = min(len(quote.text), len(seen))
                if shorter > 0:
                    overlap = len(
                        set(quote.text.lower().split()) &
                        set(seen.lower().split())
                    ) / max(
                        len(quote.text.split()),
                        len(seen.split())
                    )
                    if overlap > 0.8:
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique.append(quote)
                seen_texts.append(quote.text)

        return unique