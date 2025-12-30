"""Browser management and page crawling."""
import asyncio
import logging
import time
from playwright.async_api import async_playwright, Browser, Page
from .types import CrawlResult, CrawlStatus, CrawlerConfig

log = logging.getLogger(__name__)

class BrowserManager:
    """Manages browser lifecycle."""
    def __init__(self, cfg: CrawlerConfig) -> None:
        self.cfg = cfg
        self._pw: object | None = None
        self._browser: Browser | None = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def ensure_browser(self) -> None:
        """Ensure browser is running."""
        async with self._lock:
            if self._browser is not None:
                return
            log.info("Launching browser...")
            self._pw = await async_playwright().start()
            self._browser = await self._pw.chromium.launch(headless=True)  # type: ignore[union-attr]

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._pw:
            await self._pw.stop()  # type: ignore[union-attr]
            self._pw = None

    async def crawl_url(self, url: str) -> CrawlResult:
        """Crawl a single URL."""
        t0 = time.time()
        try:
            await self.ensure_browser()
            async with self._lock:
                if self._browser is None:
                    raise RuntimeError("Browser not available")
                ctx = await self._browser.new_context()
            page = await ctx.new_page()
            try:
                timeout_ms = int(self.cfg.page_timeout_sec * 1000)
                await page.goto(url, timeout=timeout_ms, wait_until="load")
                html = await page.content()
                rendered_bytes = len(html.encode("utf-8"))
                return CrawlResult(
                    url=url,
                    status=CrawlStatus.SUCCESS,
                    rendered_html_bytes=rendered_bytes,
                    elapsed_sec=time.time() - t0,
                )
            finally:
                await page.close()
                await ctx.close()
        except Exception as e:
            log.error(f"Crawl error for {url}: {e}")
            return CrawlResult(
                url=url,
                status=CrawlStatus.FAILED,
                error=str(e),
                elapsed_sec=time.time() - t0,
            )
