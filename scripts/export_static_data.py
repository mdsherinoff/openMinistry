"""
One-off script: extract a small public dataset from a pg_dump SQL backup
and write it out as static JSON for the frontend demo.

Reads only the ministers/statements/articles/sources tables (never users,
moderation_logs, article_queue, or mined_results). Run against a *copy* of
the backup, never the original file.

Usage:
    python scripts/export_static_data.py <path-to-postgres-backup.sql>
"""
import json
import random
import re
import sys
from pathlib import Path

SAMPLE_SIZE = 50
SEED = 42

TABLE_COLUMNS = {
    "ministers": [
        "id", "name", "name_malayalam", "portfolio", "party", "constituency",
        "start_date", "end_date", "bio", "image_url", "is_active",
        "created_at", "updated_at",
    ],
    "statements": [
        "id", "minister_id", "article_id", "statement_text",
        "statement_text_malayalam", "statement_summary", "topic",
        "sentiment", "confidence_score", "statement_date", "status",
        "reviewed_by", "reviewed_at", "created_at", "updated_at",
        "context_text", "article_context", "queue_item_id", "flagged",
        "flag_count", "flag_reason", "flagged_at",
    ],
    "articles": [
        "id", "source_id", "url", "url_hash", "title", "author",
        "published_at", "raw_content", "cleaned_content", "language",
        "scrape_status", "scraped_at", "created_at",
    ],
    "sources": [
        "id", "name", "website", "language", "credibility_score",
        "is_active", "scrape_frequency_minutes", "created_at",
    ],
}


def parse_copy_block(sql_text: str, table: str) -> list[dict]:
    match = re.search(
        rf"^COPY public\.{table} \([^)]*\) FROM stdin;\n(.*?)\n\\\.$",
        sql_text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return []
    columns = TABLE_COLUMNS[table]
    rows = []
    for line in match.group(1).split("\n"):
        if not line:
            continue
        values = line.split("\t")
        row = {}
        for col, val in zip(columns, values):
            row[col] = None if val == r"\N" else val
        rows.append(row)
    return rows


def to_int(v):
    return int(v) if v is not None else None


def to_float(v):
    return float(v) if v is not None else None


def to_iso(v):
    # pg_dump timestamps already look like "2026-06-04 23:33:58.159768+00"
    if v is None:
        return None
    return v.replace(" ", "T", 1)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-postgres-backup.sql>")
        sys.exit(1)

    backup_path = Path(sys.argv[1])
    sql_text = backup_path.read_text(encoding="utf-8")

    ministers_raw = parse_copy_block(sql_text, "ministers")
    statements_raw = parse_copy_block(sql_text, "statements")
    articles_raw = parse_copy_block(sql_text, "articles")
    sources_raw = parse_copy_block(sql_text, "sources")

    ministers_by_id = {m["id"]: m for m in ministers_raw}
    articles_by_id = {a["id"]: a for a in articles_raw}
    sources_by_id = {s["id"]: s for s in sources_raw}

    # --- ministers.json: all ministers, MinisterResponse shape ---
    ministers_out = []
    for m in ministers_raw:
        ministers_out.append({
            "id": to_int(m["id"]),
            "name": m["name"],
            "name_malayalam": m["name_malayalam"],
            "portfolio": m["portfolio"],
            "party": m["party"],
            "constituency": m["constituency"],
            "is_active": to_int(m["is_active"]),
            "start_date": m["start_date"],
            "bio": m["bio"],
            "image_url": m["image_url"],
            "created_at": to_iso(m["created_at"]),
        })
    ministers_out.sort(key=lambda m: m["name"] or "")

    # --- sample ~50 approved statements, spread across topics/ministers ---
    approved = [s for s in statements_raw if s["status"] == "approved"]

    by_topic: dict[str, list[dict]] = {}
    for s in approved:
        by_topic.setdefault(s["topic"] or "Uncategorized", []).append(s)

    rng = random.Random(SEED)
    for bucket in by_topic.values():
        rng.shuffle(bucket)

    topics_by_size = sorted(by_topic.items(), key=lambda kv: -len(kv[1]))
    sampled: list[dict] = []
    seen_ids: set[str] = set()
    round_idx = 0
    while len(sampled) < SAMPLE_SIZE:
        progressed = False
        for topic, bucket in topics_by_size:
            if round_idx < len(bucket):
                stmt = bucket[round_idx]
                if stmt["id"] not in seen_ids:
                    sampled.append(stmt)
                    seen_ids.add(stmt["id"])
                    progressed = True
                    if len(sampled) >= SAMPLE_SIZE:
                        break
        if not progressed:
            break
        round_idx += 1

    def build_statement(s: dict) -> dict:
        minister = ministers_by_id.get(s["minister_id"])
        article = articles_by_id.get(s["article_id"])
        source = sources_by_id.get(article["source_id"]) if article else None

        return {
            "id": to_int(s["id"]),
            "minister_id": to_int(s["minister_id"]),
            "article_id": to_int(s["article_id"]),
            "queue_item_id": to_int(s["queue_item_id"]),
            "statement_text": s["statement_text"],
            "statement_summary": s["statement_summary"],
            "topic": s["topic"],
            "confidence_score": to_float(s["confidence_score"]),
            "context_text": s["context_text"],
            "statement_date": to_iso(s["statement_date"]),
            "status": s["status"],
            "created_at": to_iso(s["created_at"]),
            "reviewed_at": to_iso(s["reviewed_at"]),
            "minister": {
                "id": to_int(minister["id"]) if minister else None,
                "name": minister["name"] if minister else "Unknown",
                "portfolio": minister["portfolio"] if minister else None,
                "party": minister["party"] if minister else None,
                "constituency": minister["constituency"] if minister else None,
                "image_url": minister["image_url"] if minister else None,
            },
            "source": {
                "name": source["name"] if source else None,
                "url": article["url"] if article else None,
                "title": article["title"] if article else None,
                "published_at": to_iso(article["published_at"]) if article else None,
            },
        }

    statements_out = [build_statement(s) for s in sampled]
    statements_out.sort(
        key=lambda s: s["statement_date"] or s["created_at"] or "",
        reverse=True,
    )

    out_dir = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "ministers.json").write_text(
        json.dumps(ministers_out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "statements.json").write_text(
        json.dumps(statements_out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    topic_counts: dict[str, int] = {}
    for s in statements_out:
        t = s["topic"] or "Uncategorized"
        topic_counts[t] = topic_counts.get(t, 0) + 1

    print(f"Wrote {len(ministers_out)} ministers -> {out_dir / 'ministers.json'}")
    print(f"Wrote {len(statements_out)} statements -> {out_dir / 'statements.json'}")
    print(f"Topics in sample: {topic_counts}")


if __name__ == "__main__":
    main()
