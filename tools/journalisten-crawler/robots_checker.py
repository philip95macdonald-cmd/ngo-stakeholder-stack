"""
robots.txt-Compliance-Checker.

Laedt robots.txt pro Host, cached das Ergebnis im Prozess-Speicher
und prueft vor jedem Crawl-Request, ob die URL erlaubt ist.
Respektiert Crawl-Delay aus der robots.txt.
"""

from __future__ import annotations

import logging
import time
from threading import Lock
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

log = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10.0


class RobotsChecker:
    def __init__(
        self,
        user_agent: str = "ngo-stakeholder-stack-crawler/0.1",
        default_crawl_delay: float = 1.0,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self.user_agent = user_agent
        self.default_crawl_delay = default_crawl_delay
        self.timeout = timeout
        self._parsers: dict[str, RobotFileParser | None] = {}
        self._lock = Lock()

    def _get_parser(self, base_url: str) -> RobotFileParser | None:
        parsed = urlparse(base_url)
        host = f"{parsed.scheme}://{parsed.netloc}"
        with self._lock:
            if host in self._parsers:
                return self._parsers[host]
            parser = self._fetch_robots(host)
            self._parsers[host] = parser
            return parser

    def _fetch_robots(self, base_url: str) -> RobotFileParser | None:
        robots_url = urljoin(base_url, "/robots.txt")
        try:
            resp = requests.get(robots_url, timeout=self.timeout)
            if resp.status_code == 200:
                parser = RobotFileParser()
                parser.set_url(robots_url)
                parser.parse(resp.text.splitlines())
                log.debug("Loaded robots.txt from %s", robots_url)
                return parser
            # 404 = no robots.txt = everything allowed
            return None
        except Exception as exc:
            log.warning("Could not fetch robots.txt from %s: %s", robots_url, exc)
            return None

    def is_allowed(self, url: str) -> bool:
        parser = self._get_parser(url)
        if parser is None:
            return True
        return parser.can_fetch(self.user_agent, url)

    def crawl_delay(self, url: str) -> float:
        parser = self._get_parser(url)
        if parser is None:
            return self.default_crawl_delay
        delay = parser.crawl_delay(self.user_agent)
        if delay is not None:
            return float(delay)
        return self.default_crawl_delay
