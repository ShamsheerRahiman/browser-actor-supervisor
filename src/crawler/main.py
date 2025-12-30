"""Main crawler orchestration."""
import asyncio
import json
import logging
import sys
from pathlib import Path
from .types import CrawlResult, CrawlStatus, CrawlerConfig
from .browser import BrowserManager

log = logging.getLogger(__name__)

def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

def load_urls(path: Path, limit: int | None = None) -> list[str]:
    urls = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if limit:
        urls = urls[:limit]
    log.info(f"Loaded {len(urls)} URLs from {path}")
    return urls

def save_results(results: list[CrawlResult], path: Path) -> None:
    data = [
        {
            "url": r.url,
            "status": r.status.name,
            "initial_html_bytes": r.initial_html_bytes,
            "rendered_html_bytes": r.rendered_html_bytes,
            "error": r.error,
        }
        for r in results
    ]
    path.write_text(json.dumps(data, indent=2))
    log.info(f"Saved {len(results)} results to {path}")

async def main() -> None:
    setup_logging()
    cfg = CrawlerConfig()
    n_urls = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    url_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("REF_context/2kurls.txt")
    urls = load_urls(url_file, limit=n_urls)
    browser = BrowserManager(cfg)
    results = []
    try:
        for url in urls:
            result = await browser.crawl_url(url)
            results.append(result)
            log.info(f"Crawled {url}: {result.status.name}")
    finally:
        await browser.close()
    save_results(results, Path("crawl_results.json"))

if __name__ == "__main__":
    asyncio.run(main())
