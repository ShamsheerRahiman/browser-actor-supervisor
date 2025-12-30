"""Domain-based scheduling for per-domain delays."""
import logging
import time
from collections import defaultdict
from urllib.parse import urlparse
from .types import DomainState, CrawlerConfig

log = logging.getLogger(__name__)

def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc or url

class DomainScheduler:
    """Schedules URLs respecting per-domain delays."""
    def __init__(self, cfg: CrawlerConfig) -> None:
        self.cfg = cfg
        self.domains: dict[str, DomainState] = defaultdict(
            lambda: DomainState(domain="")
        )
        self._in_flight: set[str] = set()
    def add_urls(self, urls: list[str]) -> None:
        """Add URLs to the scheduler."""
        for url in urls:
            domain = extract_domain(url)
            if domain not in self.domains:
                self.domains[domain] = DomainState(domain=domain)
            self.domains[domain].pending_urls.append(url)
        log.info(f"Added {len(urls)} URLs across {len(self.domains)} domains.")
    def get_ready_urls(self) -> list[str]:
        """Get all URLs ready to crawl (domains past delay and not in-flight)."""
        ready: list[str] = []
        now = time.time()
        for domain, state in self.domains.items():
            if not state.pending_urls:
                continue
            if domain in self._in_flight:
                continue
            if now - state.last_crawl_ts >= self.cfg.domain_delay_sec:
                url = state.pending_urls.pop(0)
                self._in_flight.add(domain)
                ready.append(url)
        return ready
    def mark_done(self, url: str) -> None:
        """Mark URL as done: remove from in-flight, start cooldown."""
        domain = extract_domain(url)
        self._in_flight.discard(domain)
        if domain in self.domains:
            self.domains[domain].last_crawl_ts = time.time()
    def n_pending(self) -> int:
        """Count total pending URLs."""
        return sum(len(s.pending_urls) for s in self.domains.values())
    def n_in_flight(self) -> int:
        """Count domains currently being crawled."""
        return len(self._in_flight)
    def next_available_sec(self) -> float:
        """Seconds until next domain is ready."""
        if self.n_pending() == 0:
            return 0.0
        now = time.time()
        min_wait = float("inf")
        for domain, state in self.domains.items():
            if state.pending_urls and domain not in self._in_flight:
                wait = self.cfg.domain_delay_sec - (now - state.last_crawl_ts)
                min_wait = min(min_wait, max(0.0, wait))
        return min_wait if min_wait != float("inf") else 0.0

