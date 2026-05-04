import logging
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

FEEDS_INDEX_URL = "https://saasedl.paloaltonetworks.com/feeds.html"
logger = logging.getLogger(__name__)

REGION_KEYWORDS = [
    "/germany/",
    "/eu/",
    "/eu-west/",
    "/eu-central/",
    "/eu-north/",
    "/eu-south/",
    "/global/",
    "/all/",
    "/worldwide/",
]


def _is_target_region(url: str) -> bool:
    """Check if URL belongs to Europe/Germany/Worldwide regions."""
    url_lower = url.lower()
    return any(kw in url_lower for kw in REGION_KEYWORDS)


def discover_ipv4_feeds() -> List[Tuple[str, str]]:
    """Discover all IPv4 EDL feeds from the Palo Alto feeds index page.

    Only returns feeds from Europe, Germany, and Worldwide/Global/All regions.

    Returns:
        List of tuples: (feed_name, feed_url)
    """
    logger.info(f"Fetching feeds index from {FEEDS_INDEX_URL}")
    resp = requests.get(FEEDS_INDEX_URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    feeds = []
    seen_urls = set()

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            name_cell = cells[0].get_text(strip=True)
            link = cells[1].find("a")

            if not link:
                continue

            url = link.get("href", "")
            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            full_url = url if url.startswith("http") else f"https://saasedl.paloaltonetworks.com{url}"

            if "/ipv4" in url and _is_target_region(url):
                feeds.append((name_cell, full_url))
                logger.debug(f"Found feed: {name_cell} -> {full_url}")

    logger.info(f"Discovered {len(feeds)} IPv4 feeds (Europe/Germany/Worldwide)")
    return feeds
