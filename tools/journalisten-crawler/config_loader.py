"""
Config-Loader fuer den journalisten-crawler.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.config_loader import get  # noqa: E402


class CrawlerConfig:
    """Wrapper fuer einfacheren Zugriff."""

    def __init__(self) -> None:
        self.domains_de = get("journalisten.domains_de", default=[])
        self.domains_eu = get("journalisten.domains_eu", default=[])
        self.cap_per_domain = get("journalisten.cap_per_domain", default=50)
        self.rate_limit_seconds = get("journalisten.rate_limit_seconds", default=1.0)
        self.user_agent = get(
            "journalisten.user_agent",
            default="ngo-stakeholder-stack-crawler/0.1",
        )
        self.respect_robots_txt = get("journalisten.respect_robots_txt", default=True)
        self.follow_publisher_groups = get("journalisten.follow_publisher_groups", default=True)


def load_config() -> CrawlerConfig:
    return CrawlerConfig()


if __name__ == "__main__":
    cfg = load_config()
    print(f"DE Domains: {len(cfg.domains_de)}")
    print(f"EU Domains: {len(cfg.domains_eu)}")
    print(f"Cap pro Domain: {cfg.cap_per_domain}")
    print(f"User-Agent: {cfg.user_agent}")
