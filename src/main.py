import argparse
import ipaddress
import logging
import sys
from typing import List, Tuple, Union

from src.edl_checker import check_ip_against_feeds
from src.feeds import discover_ipv4_feeds


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_target(ip_str: str) -> Union[ipaddress.IPv4Address, ipaddress.IPv4Network]:
    """Parse an IPv4 address or CIDR network string."""
    try:
        if "/" in ip_str:
            return ipaddress.IPv4Network(ip_str, strict=False)
        return ipaddress.IPv4Address(ip_str)
    except ValueError:
        raise ValueError(f"Invalid IPv4 address or network: {ip_str}")


def print_results(
    target,
    matches: List[Tuple[str, str, list]],
) -> None:
    if not matches:
        print(f"\n{target} not found in any Palo Alto EDL feeds.")
        return

    print(f"\n{target} found in {len(matches)} EDL feed(s):\n")
    print("-" * 80)
    for feed_name, feed_url, subnets in matches:
        print(f"  Name: {feed_name}")
        print(f"  URL:  {feed_url}")
        print(f"  Matching subnets ({len(subnets)}):")
        for subnet in subnets:
            print(f"    - {subnet}")
        print("-" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Palo Alto EDL IP Lookup Tool - Check if an IP is in any Palo Alto EDL list"
    )
    parser.add_argument(
        "ip",
        help="IPv4 address or network to check (e.g., 52.123.224.73 or 52.123.224.0/24)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug output",
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    try:
        target = parse_target(args.ip)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Discovering Palo Alto EDL feeds...")
    feeds = discover_ipv4_feeds()
    print(f"Found {len(feeds)} IPv4 feeds. Checking {target}...")

    matches = check_ip_against_feeds(target, feeds)
    print_results(target, matches)


if __name__ == "__main__":
    main()
