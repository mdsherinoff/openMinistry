"""
Source configuration registry.
Each entry defines how to scrape a specific news source.
"""

SOURCE_CONFIGS = {
    # "mathrubhumi.com": {
    #     "name": "Mathrubhumi",
    #     "base_url": "https://www.mathrubhumi.com",
    #     "language": "ml",
    #     "article_list_urls": [
    #         "https://www.mathrubhumi.com/news/kerala",
    #         "https://www.mathrubhumi.com/news/india",
    #     ],
    #     "selectors": {
    #         "article_links": "a[href*='/news/']",
    #         "title": "h1.article-title, h1.title",
    #         "content": "div.article-body, div.story-content",
    #         "author": "span.author-name, div.author",
    #         "date": "time[datetime], span.date",
    #     },
    #     "scrape_frequency_minutes": 15,
    #     "credibility_score": 0.9,
    #     "requires_js": False,
    # },

    # "onmanorama.com": {
    #     "name": "Manorama Online",
    #     "base_url": "https://www.onmanorama.com",
    #     "language": "ml",
    #     "article_list_urls": [
    #         "https://www.onmanorama.com/news/kerala.html",
    #         "https://www.onmanorama.com/news/india.html",
    #     ],
    #     "selectors": {
    #         "article_links": "a[href*='/news/']",
    #         "title": "h1.article-title, h1",
    #         "content": "div.article-body, div.story-body",
    #         "author": "span.author, div.byline",
    #         "date": "time[datetime], span.published-date",
    #     },
    #     "scrape_frequency_minutes": 15,
    #     "credibility_score": 0.9,
    #     "requires_js": False,
    # },

    "thehindu.com": {
        "name": "The Hindu - Kerala",
        "base_url": "https://www.thehindu.com",
        "language": "en",
        "article_list_urls": [
            "https://www.thehindu.com/news/national/kerala/",
        ],
        "scrape_frequency_minutes": 30,
        "credibility_score": 0.95,
    },
}

def get_source_config(domain: str) -> dict | None:
    for key, config in SOURCE_CONFIGS.items():
        if key in domain:
            return config
    return None

def get_all_active_configs() -> list[dict]:
    return list(SOURCE_CONFIGS.values())