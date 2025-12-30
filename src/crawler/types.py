"""Types and models for the crawler."""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import NamedTuple
import time

class CrawlStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    SUCCESS = auto()
    FAILED = auto()
    TIMEOUT = auto()

@dataclass(slots=True)
class CrawlResult:
    """Result of crawling a single URL."""
    url: str
    status: CrawlStatus
    initial_html_bytes: int = 0
    rendered_html_bytes: int = 0
    error: str | None = None
    elapsed_sec: float = 0.0

@dataclass(slots=True)
class DomainState:
    """Tracks per-domain crawl state."""
    domain: str
    last_crawl_ts: float = 0.0
    pending_urls: list[str] = field(default_factory=list)
    def can_crawl(self, delay_sec: float = 60.0) -> bool:
        return time.time() - self.last_crawl_ts >= delay_sec
    def mark_crawled(self) -> None:
        self.last_crawl_ts = time.time()

class ResourceStats(NamedTuple):
    """System resource statistics."""
    cpu_pct: float
    mem_pct: float
    mem_avail_mb: float

@dataclass(slots=True)
class CrawlerConfig:
    """Crawler configuration."""
    domain_delay_sec: float = 60.0
    page_timeout_sec: float = 60.0
    cpu_threshold: float = 80.0
    mem_threshold: float = 80.0
    min_mem_avail_mb: float = 512.0
