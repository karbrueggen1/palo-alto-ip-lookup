import ipaddress
import unittest
from unittest.mock import patch, MagicMock

from src.edl_checker import check_ip_against_feeds, fetch_edl_subnets
from src.main import parse_target


class TestParseTarget(unittest.TestCase):
    def test_single_ip(self):
        result = parse_target("52.123.224.73")
        self.assertEqual(result, ipaddress.IPv4Address("52.123.224.73"))

    def test_cidr_network(self):
        result = parse_target("52.123.224.0/24")
        self.assertEqual(result, ipaddress.IPv4Network("52.123.224.0/24", strict=False))

    def test_invalid_ip(self):
        with self.assertRaises(ValueError):
            parse_target("999.999.999.999")

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            parse_target("not-an-ip")


class TestFetchEdlSubnets(unittest.TestCase):
    @patch("src.edl_checker.requests.get")
    def test_parse_valid_subnets(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "10.0.0.0/24\n192.168.1.0/24\n"
        mock_get.return_value = mock_response

        subnets = fetch_edl_subnets("http://example.com/ipv4")
        self.assertEqual(len(subnets), 2)
        self.assertIn(ipaddress.IPv4Network("10.0.0.0/24"), subnets)
        self.assertIn(ipaddress.IPv4Network("192.168.1.0/24"), subnets)

    @patch("src.edl_checker.requests.get")
    def test_skip_comments_and_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "# comment\n\n10.0.0.0/24\n"
        mock_get.return_value = mock_response

        subnets = fetch_edl_subnets("http://example.com/ipv4")
        self.assertEqual(len(subnets), 1)


class TestCheckIpAgainstFeeds(unittest.TestCase):
    @patch("src.edl_checker.fetch_edl_subnets")
    def test_ip_found_in_feed(self, mock_fetch):
        mock_fetch.return_value = [ipaddress.IPv4Network("10.0.0.0/8")]
        feeds = [("Test Feed", "http://example.com/ipv4")]

        matches = check_ip_against_feeds(ipaddress.IPv4Address("10.1.2.3"), feeds)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "Test Feed")

    @patch("src.edl_checker.fetch_edl_subnets")
    def test_ip_not_found_in_feed(self, mock_fetch):
        mock_fetch.return_value = [ipaddress.IPv4Network("10.0.0.0/8")]
        feeds = [("Test Feed", "http://example.com/ipv4")]

        matches = check_ip_against_feeds(ipaddress.IPv4Address("192.168.1.1"), feeds)
        self.assertEqual(len(matches), 0)

    @patch("src.edl_checker.fetch_edl_subnets")
    def test_network_overlap(self, mock_fetch):
        mock_fetch.return_value = [ipaddress.IPv4Network("10.0.0.0/8")]
        feeds = [("Test Feed", "http://example.com/ipv4")]

        matches = check_ip_against_feeds(ipaddress.IPv4Network("10.1.0.0/16"), feeds)
        self.assertEqual(len(matches), 1)

    @patch("src.edl_checker.fetch_edl_subnets")
    def test_multiple_feeds(self, mock_fetch):
        mock_fetch.side_effect = [
            [ipaddress.IPv4Network("10.0.0.0/8")],
            [ipaddress.IPv4Network("192.168.0.0/16")],
        ]
        feeds = [
            ("Feed A", "http://a.com/ipv4"),
            ("Feed B", "http://b.com/ipv4"),
        ]

        matches = check_ip_against_feeds(ipaddress.IPv4Address("10.1.2.3"), feeds)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "Feed A")


if __name__ == "__main__":
    unittest.main()
