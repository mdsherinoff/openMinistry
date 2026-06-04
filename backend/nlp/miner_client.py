"""
Client for calling the open-ministry-miner API.
Handles all communication between openMinistry and the miner service.
"""
import logging
import httpx
import os
from typing import Optional

logger = logging.getLogger(__name__)

MINER_URL = os.environ.get("MINER_URL", "http://localhost:8001")


def mine_url(url: str, timeout: int = 120) -> dict:
    """
    Send a URL to the miner and get back structured extraction.
    Returns the full miner response dict.
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            res = client.post(
                f"{MINER_URL}/mine",
                json={"url": url},
            )
            res.raise_for_status()
            return res.json()
    except httpx.TimeoutException:
        raise Exception(f"Miner timed out processing {url}")
    except httpx.HTTPStatusError as e:
        raise Exception(
            f"Miner returned {e.response.status_code} for {url}"
        )
    except Exception as e:
        raise Exception(f"Miner error: {e}")


def is_miner_available() -> bool:
    """Check if the miner service is reachable."""
    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.get(f"{MINER_URL}/")
            return res.status_code == 200
    except Exception:
        return False


def parse_speaker_briefs(annotation: dict) -> list[dict]:
    """
    Parse the miner's annotation output into
    a flat list of statement candidates.
    """
    results = []
    speaker_briefs = annotation.get("speaker_briefs", [])

    for brief in speaker_briefs:
        speaker_name = brief.get("speaker_name", "").strip()
        speaker_role = brief.get("speaker_role", "").strip()
        quality_stars = brief.get("extraction_quality_stars", 3)
        topics = brief.get("topics", [])
        context_description = brief.get("combined_context_description", "")

        for stmt in brief.get("statements", []):
            text = stmt.get("snippet", "").strip()
            if not text or len(text) < 15:
                continue

            topic_tag = stmt.get("topic_tag", "")
            stmt_context = stmt.get("context_description", "")

            results.append({
                "speaker_name": speaker_name,
                "speaker_role": speaker_role,
                "statement_text": text,
                "context_description": stmt_context or context_description,
                "topic_tag": topic_tag,
                "confidence_stars": quality_stars,
                "brief_topics": topics,
            })

    return results