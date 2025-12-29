"""Types and models for the crawler."""
from dataclasses import dataclass
from enum import Enum, auto

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