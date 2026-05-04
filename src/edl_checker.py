import ipaddress
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Tuple, Union

import requests

logger = logging.getLogger(__name__)

MAX_WORKERS = 50


def fetch_edl_subnets(url: str) -> List[ipaddress.IPv4Network]:
    """Fetch and parse subnets from an EDL URL.

    Returns:
        List of IPv4Network objects
    """
    logger.debug(f"Fetching EDL from {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    networks = []
    for line in resp.text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            networks.append(ipaddress.IPv4Network(line, strict=False))
        except ValueError:
            logger.warning(f"Invalid subnet entry: {line}")

    logger.debug(f"Parsed {len(networks)} subnets from {url}")
    return networks


def _check_single_feed(
    target: Union[ipaddress.IPv4Address, ipaddress.IPv4Network],
    feed_name: str,
    feed_url: str,
) -> Union[Tuple[str, str, List[ipaddress.IPv4Network]], None]:
    """Check if target IP is in a single feed. Returns match or None."""
    try:
        subnets = fetch_edl_subnets(feed_url)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {feed_url}: {e}")
        return None

    matching_subnets = []
    for subnet in subnets:
        if isinstance(target, ipaddress.IPv4Address):
            if target in subnet:
                matching_subnets.append(subnet)
        else:
            if target.overlaps(subnet):
                matching_subnets.append(subnet)

    if matching_subnets:
        return (feed_name, feed_url, matching_subnets)
    return None


def check_ip_against_feeds(
    target: Union[ipaddress.IPv4Address, ipaddress.IPv4Network],
    feeds: List[Tuple[str, str]],
) -> List[Tuple[str, str, List[ipaddress.IPv4Network]]]:
    """Check if an IP or network is contained in any of the EDL feeds.

    Uses concurrent requests to check all feeds in parallel.

    Args:
        target: IPv4 address or network to check
        feeds: List of (name, url) tuples

    Returns:
        List of (feed_name, feed_url, matching_subnets) for feeds containing the target
    """
    matches = []
    checked = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_check_single_feed, target, name, url): (name, url)
            for name, url in feeds
        }

        for future in as_completed(futures):
            checked += 1
            result = future.result()
            if result is not None:
                matches.append(result)
            if checked % 100 == 0:
                logger.info(f"Checked {checked}/{len(feeds)} feeds...")

    logger.info(f"Checked all {len(feeds)} feeds. Found {len(matches)} matches.")
    return matches
