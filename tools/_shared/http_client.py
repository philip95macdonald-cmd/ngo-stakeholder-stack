"""
Konservativer HTTP-Client mit:
  - Sinnvollen Timeouts (Default 30s)
  - Retry mit Exponential Backoff (3 Versuche bei 5xx und Timeouts)
  - Custom User-Agent aus Config
  - Per-Host Rate-Limit (Token-Bucket)
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from threading import Lock
from typing import Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)


class RateLimiter:
    """Per-Host Throttling mit Token-Bucket-Lite. Eine Anfrage alle X Sekunden."""

    def __init__(self, seconds_between: float = 1.0) -> None:
        self.seconds_between = seconds_between
        self._last: dict[str, float] = defaultdict(lambda: 0.0)
        self._lock = Lock()

    def acquire(self, url: str) -> None:
        host = urlparse(url).netloc
        with self._lock:
            elapsed = time.monotonic() - self._last[host]
            wait = self.seconds_between - elapsed
            if wait > 0:
                time.sleep(wait)
            self._last[host] = time.monotonic()


def make_session(
    user_agent: str = "ngo-stakeholder-stack/0.1",
    retries: int = 3,
    backoff: float = 0.5,
) -> requests.Session:
    """Liefert eine Session mit Retry-Adapter."""
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": user_agent,
            "Accept-Language": "de,en;q=0.7",
        }
    )
    retry = Retry(
        total=retries,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=backoff,
        allowed_methods=["GET", "HEAD"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


class Client:
    """High-level Wrapper: GET mit Rate-Limit + Retry + sinnvollen Defaults."""

    def __init__(
        self,
        user_agent: str = "ngo-stakeholder-stack/0.1",
        rate_limit_seconds: float = 1.0,
        timeout: float = 30.0,
    ) -> None:
        self.session = make_session(user_agent=user_agent)
        self.limiter = RateLimiter(rate_limit_seconds)
        self.timeout = timeout

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        self.limiter.acquire(url)
        kwargs.setdefault("timeout", self.timeout)
        log.debug("GET %s", url)
        return self.session.get(url, **kwargs)

    def get_json(self, url: str, **kwargs: Any) -> dict[str, Any]:
        r = self.get(url, **kwargs)
        r.raise_for_status()
        return r.json()
