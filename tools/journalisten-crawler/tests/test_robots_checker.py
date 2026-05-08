"""Tests fuer den Robots-Checker."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from robots_checker import RobotsChecker


def _mock_robots_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.text = text
    return resp


ROBOTS_TXT = """
User-agent: *
Disallow: /admin/
Crawl-delay: 2

User-agent: ngo-stakeholder-stack-crawler/0.1
Allow: /presse/
Disallow: /intern/
"""


class TestRobotsChecker:
    def _checker(self) -> RobotsChecker:
        return RobotsChecker(user_agent="ngo-stakeholder-stack-crawler/0.1", default_crawl_delay=1.0)

    def test_allowed_path(self):
        checker = self._checker()
        with patch("robots_checker.requests.get", return_value=_mock_robots_response(ROBOTS_TXT)):
            assert checker.is_allowed("https://beispiel.de/presse/kontakt") is True

    def test_disallowed_admin(self):
        checker = self._checker()
        with patch("robots_checker.requests.get", return_value=_mock_robots_response(ROBOTS_TXT)):
            assert checker.is_allowed("https://beispiel.de/admin/panel") is False

    def test_crawl_delay_from_robots(self):
        checker = self._checker()
        with patch("robots_checker.requests.get", return_value=_mock_robots_response(ROBOTS_TXT)):
            delay = checker.crawl_delay("https://beispiel.de/")
            assert delay >= 1.0

    def test_no_robots_txt_allows_all(self):
        checker = self._checker()
        resp_404 = MagicMock()
        resp_404.status_code = 404
        with patch("robots_checker.requests.get", return_value=resp_404):
            assert checker.is_allowed("https://beispiel.de/anything") is True

    def test_fetch_error_allows_all(self):
        checker = self._checker()
        with patch("robots_checker.requests.get", side_effect=ConnectionError("timeout")):
            assert checker.is_allowed("https://beispiel.de/presse") is True

    def test_caching(self):
        checker = self._checker()
        with patch("robots_checker.requests.get", return_value=_mock_robots_response(ROBOTS_TXT)) as mock:
            checker.is_allowed("https://beispiel.de/a")
            checker.is_allowed("https://beispiel.de/b")
            # Only one HTTP request for robots.txt (cached)
            assert mock.call_count == 1

    def test_default_crawl_delay_fallback(self):
        checker = RobotsChecker(default_crawl_delay=3.0)
        resp = MagicMock()
        resp.status_code = 404
        with patch("robots_checker.requests.get", return_value=resp):
            assert checker.crawl_delay("https://beispiel.de/") == 3.0
