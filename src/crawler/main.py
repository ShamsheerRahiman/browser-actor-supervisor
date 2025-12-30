"""Main crawler orchestration."""
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto
from .actor import Actor, ActorEnv
from .types import CrawlResult, CrawlStatus, CrawlerConfig
from .browser import BrowserManager
from .scheduler import DomainScheduler
from .monitor import ResourceMonitor

log = logging.getLogger(__name__)

def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

def load_urls(path: Path, limit: int | None = None) -> list[str]:
    """Load URLs from file."""
    urls = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if limit:
        urls = urls[:limit]
    log.info(f"Loaded {len(urls)} URLs from {path}")
    return urls

def save_results(results: list[CrawlResult], path: Path, wall_clock_sec: float = 0.0) -> None:
    """Save results to JSON with metadata."""
    data = {
        "metadata": {
            "wall_clock_sec": round(wall_clock_sec, 2),
            "n_urls": len(results),
        },
        "results": [
            {
                "url": r.url,
                "status": r.status.name,
                "initial_html_bytes": r.initial_html_bytes,
                "rendered_html_bytes": r.rendered_html_bytes,
                "error": r.error,
                "elapsed_sec": round(r.elapsed_sec, 2),
            }
            for r in results
        ],
    }
    path.write_text(json.dumps(data, indent=2))
    log.info(f"Saved {len(results)} results to {path}")

def print_stats(results: list[CrawlResult]) -> None:
    """Print summary statistics."""
    n_total = len(results)
    n_success = sum(1 for r in results if r.status == CrawlStatus.SUCCESS)
    n_timeout = sum(1 for r in results if r.status == CrawlStatus.TIMEOUT)
    n_failed = sum(1 for r in results if r.status == CrawlStatus.FAILED)
    init_bytes = [r.initial_html_bytes for r in results if r.initial_html_bytes > 0]
    rend_bytes = [r.rendered_html_bytes for r in results if r.rendered_html_bytes > 0]
    print(f"\n=== Crawl Stats ===")
    print(f"Total: {n_total}, Success: {n_success}, Timeout: {n_timeout}, Failed: {n_failed}")
    if init_bytes:
        print(f"Initial HTML: min={min(init_bytes)}, max={max(init_bytes)}, avg={sum(init_bytes)//len(init_bytes)}")
    if rend_bytes:
        print(f"Rendered HTML: min={min(rend_bytes)}, max={max(rend_bytes)}, avg={sum(rend_bytes)//len(rend_bytes)}")

class Crawler:
    """Main crawler orchestrator."""
    def __init__(self, cfg: CrawlerConfig) -> None:
        self.cfg = cfg
        self.browser = BrowserManager(cfg)
        self.scheduler = DomainScheduler(cfg)
        self.monitor = ResourceMonitor(cfg)
        self.results: list[CrawlResult] = []
        self._active_tasks: set[asyncio.Task[CrawlResult]] = set()
    async def run(self, urls: list[str]) -> list[CrawlResult]:
        """Run crawler on URLs."""
        self.scheduler.add_urls(urls)
        try:
            await self._crawl_loop()
        finally:
            await self.browser.close()
        return self.results
    async def _crawl_loop(self) -> None:
        """Main crawl loop."""
        while self.scheduler.n_pending() > 0 or self._active_tasks:
            done = {t for t in self._active_tasks if t.done()}
            for t in done:
                try:
                    result = t.result()
                    self.results.append(result)
                    self.scheduler.mark_done(result.url)
                except Exception as e:
                    log.error(f"Task error: {e}")
            self._active_tasks -= done
            n_active = len(self._active_tasks)
            if self.monitor.can_launch_more(n_active):
                ready = self.scheduler.get_ready_urls()
                if ready:
                    log.info(f"[concurrency] launching {len(ready)} new tasks, active={n_active}→{n_active+len(ready)}")
                for url in ready:
                    task = asyncio.create_task(self.browser.crawl_url(url))
                    self._active_tasks.add(task)
                    log.info(f"[start] {url}")
            if self._active_tasks:
                await asyncio.sleep(0.5)
            else:
                wait = self.scheduler.next_available_sec()
                if wait > 0:
                    log.info(f"Waiting {wait:.1f}s for next domain...")
                    await asyncio.sleep(min(wait, 5.0))

@dataclass(slots=True)
class RunRequest:
    urls: list[str]


class NoCast(Enum):
    NONE = auto()


class CrawlerActor(Actor[RunRequest, NoCast, list[CrawlResult]]):
    def __init__(self, cfg: CrawlerConfig) -> None:
        self.cfg = cfg
        self._crawler = Crawler(cfg)

    async def init(self, _env: ActorEnv[RunRequest, NoCast, list[CrawlResult]]) -> None:
        return

    async def handle_call(
        self,
        msg: RunRequest,
        _env: ActorEnv[RunRequest, NoCast, list[CrawlResult]],
        reply_sender,
    ) -> None:
        results = await self._crawler.run(msg.urls)
        reply_sender.send(results)

    async def before_exit(
        self,
        _run_result: Exception | None,
        _env: ActorEnv[RunRequest, NoCast, list[CrawlResult]],
    ) -> Exception | None:
        await self._crawler.browser.close()
        return None

async def main() -> None:
    """Entry point."""
    setup_logging()
    cfg = CrawlerConfig(
        domain_delay_sec=60.0,
        page_timeout_sec=60.0,
    )
    n_urls = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    url_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("REF_context/2kurls.txt")
    urls = load_urls(url_file, limit=n_urls)
    actor = CrawlerActor(cfg)
    actor_ref = actor.spawn()
    t0 = time.time()
    results = await actor_ref.call(RunRequest(urls))
    wall_clock = time.time() - t0
    actor_ref.cancel()
    save_results(results, Path("crawl_results.json"), wall_clock)
    print_stats(results)

if __name__ == "__main__":
    asyncio.run(main())
