import ipaddress
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Union

import requests

logger = logging.getLogger(__name__)

MAX_WORKERS = 50


def fetch_edl_subnets(url: str) -> List[ipaddress.IPv4Network]:
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


def preload_subnets(
    feeds: List[Tuple[str, str]],
) -> Dict[str, List[ipaddress.IPv4Network]]:
    """Fetch all feed subnets in parallel and return a url→subnets mapping."""
    result: Dict[str, List[ipaddress.IPv4Network]] = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_edl_subnets, url): url for _, url in feeds}
        loaded = 0
        for future in as_completed(futures):
            url = futures[future]
            loaded += 1
            try:
                result[url] = future.result()
            except requests.RequestException as e:
                logger.error(f"Failed to fetch {url}: {e}")
                result[url] = []
            if loaded % 50 == 0:
                logger.info(f"Preloaded {loaded}/{len(feeds)} feeds...")

    logger.info(f"Preloaded all {len(feeds)} feeds.")
    return result


def check_ip_against_cache(
    target: Union[ipaddress.IPv4Address, ipaddress.IPv4Network],
    feeds: List[Tuple[str, str]],
    subnet_cache: Dict[str, List[ipaddress.IPv4Network]],
) -> List[Tuple[str, str, List[ipaddress.IPv4Network]]]:
    """Check target against the in-memory subnet cache. No network I/O."""
    matches = []
    for name, url in feeds:
        subnets = subnet_cache.get(url, [])
        matching = [
            s for s in subnets
            if (target in s if isinstance(target, ipaddress.IPv4Address) else target.overlaps(s))
        ]
        if matching:
            matches.append((name, url, matching))

    logger.info(f"Checked {len(feeds)} feeds. Found {len(matches)} matches.")
    return matches
