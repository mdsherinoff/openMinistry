import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TopicClassifier:
    """
    Classifies statements into topics using keyword matching.
    Simple and reliable — no ML needed for MVP.
    """

    TOPICS = {
        "Health": [
            "hospital", "health", "doctor", "medicine", "medical",
            "healthcare", "patient", "disease", "treatment", "clinic",
            "ambulance", "dengue", "covid", "vaccine", "nursing",
            "pharmacy", "surgery", "cancer", "mental health", "ayush",
            "ayurveda", "drug", "epidemic", "outbreak", "health centre",
        ],
        "Education": [
            "school", "college", "university", "education", "student",
            "teacher", "curriculum", "exam", "textbook", "scholarship",
            "literacy", "classroom", "academic", "degree", "campus",
            "syllabus", "admission", "higher education", "research",
            "coaching", "tuition", "ktet", "sslc", "plus two",
        ],
        "Transport": [
            "road", "highway", "bridge", "transport", "bus", "train",
            "railway", "airport", "metro", "traffic", "vehicle",
            "driving", "ksrtc", "expressway", "flyover", "tunnel",
            "port", "shipping", "aviation", "ferry", "waterway",
            "national highway", "bypass", "rail", "vizhinjam",
        ],
        "Economy": [
            "economy", "budget", "finance", "investment", "industry",
            "employment", "job", "salary", "tax", "revenue", "gdp",
            "trade", "business", "startup", "msme", "export", "import",
            "inflation", "poverty", "loan", "bank", "fiscal",
            "expenditure", "allocation", "scheme", "subsidy",
        ],
        "Agriculture": [
            "farmer", "agriculture", "crop", "harvest", "irrigation",
            "paddy", "rice", "vegetable", "fruit", "plantation",
            "rubber", "coconut", "spice", "fishery", "fishing",
            "livestock", "dairy", "soil", "fertilizer", "pesticide",
            "agricultural", "aquaculture", "watershed", "farm",
        ],
        "Environment": [
            "environment", "forest", "wildlife", "pollution", "climate",
            "water", "river", "lake", "flood", "landslide", "drought",
            "green", "solar", "renewable", "ecology", "biodiversity",
            "conservation", "waste", "plastic", "emission", "carbon",
            "tree", "deforestation", "sanctuary", "national park",
        ],
        "Infrastructure": [
            "infrastructure", "construction", "building", "project",
            "development", "smart city", "urban", "rural", "housing",
            "electricity", "power", "water supply", "sewage", "drainage",
            "internet", "broadband", "tower", "cable", "pipeline",
            "k-rail", "silverline", "corridor",
        ],
        "Law & Order": [
            "police", "crime", "arrest", "court", "law", "justice",
            "investigation", "accused", "murder", "theft", "fraud",
            "corruption", "vigilance", "enforcement", "raid", "custody",
            "prosecution", "legal", "high court", "supreme court",
            "verdict", "case", "complaint", "fir",
        ],
        "Social Welfare": [
            "welfare", "pension", "social", "women", "child",
            "disability", "elderly", "sc", "st", "obc", "tribal",
            "minority", "backward", "reservation", "scholarship",
            "housing scheme", "ration", "pds", "poverty", "homeless",
            "orphan", "widow", "kudumbashree",
        ],
        "Politics": [
            "election", "party", "government", "opposition", "vote",
            "assembly", "parliament", "minister", "mla", "mp",
            "campaign", "manifesto", "alliance", "coalition", "rally",
            "protest", "demonstration", "ldf", "udf", "bjp", "congress",
            "cpm", "cpim", "iuml", "kerala congress",
        ],
        "Tourism": [
            "tourism", "tourist", "travel", "hotel", "resort",
            "heritage", "culture", "festival", "beach", "backwater",
            "hill station", "pilgrimage", "temple", "church", "mosque",
            "art", "museum", "monument", "destination", "onam",
            "vishu", "thrissur pooram",
        ],
        "Finance": [
            "budget", "allocation", "crore", "lakh", "fund",
            "expenditure", "revenue", "tax", "gst", "deficit",
            "debt", "loan", "interest", "fiscal", "treasury",
            "grant", "financial", "rupee", "payment", "transfer",
        ],
    }

    def classify(self, text: str) -> Optional[str]:
        """
        Classify a statement into a topic.
        Returns the best matching topic or None.
        """
        if not text:
            return None

        text_lower = text.lower()
        scores = {}

        for topic, keywords in self.TOPICS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Longer keywords = higher confidence
                    score += len(keyword.split())
            if score > 0:
                scores[topic] = score

        if not scores:
            return None

        # Return highest scoring topic
        return max(scores, key=scores.get)

    def classify_batch(self, texts: list[str]) -> list[Optional[str]]:
        """Classify a list of statements."""
        return [self.classify(text) for text in texts]

    def get_all_topics(self) -> list[str]:
        """Return all available topic names."""
        return list(self.TOPICS.keys())