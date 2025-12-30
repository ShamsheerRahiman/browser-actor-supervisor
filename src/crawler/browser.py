"""Browser management and page crawling."""
import asyncio
import logging
import time
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response
from .types import CrawlResult, CrawlStatus, CrawlerConfig

log = logging.getLogger(__name__)

class BrowserManager:
    """Manages browser lifecycle with restart on failure."""
    def __init__(self, cfg: CrawlerConfig) -> None:
        self.cfg = cfg
        self._pw: object | None = None  # type: ignore[assignment]
        self._browser: Browser | None = None
        self._ctx: BrowserContext | None = None
        self._n_failures: int = 0
        self._max_failures: int = 3
        self._lock: asyncio.Lock = asyncio.Lock()
    async def ensure_browser(self) -> None:
        """Ensure browser is running."""
        async with self._lock:
            if self._browser is not None:
                return
            log.info("Launching browser...")
            self._pw = await async_playwright().start()
            self._browser = await self._pw.chromium.launch(headless=True)  # type: ignore[union-attr]
            self._n_failures = 0
    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._ctx:
            await self._ctx.close()
            self._ctx = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._pw:
            await self._pw.stop()  # type: ignore[union-attr]
            self._pw = None
    async def restart(self) -> None:
        """Restart browser."""
        async with self._lock:
            if self._ctx is None:
                return
            log.warning("Restarting browser...")
            await self.close()
        await self.ensure_browser()
    async def on_failure(self, error_msg: str) -> None:
        """Handle failure, restart only on repeated non-browser-closed errors."""
        if "browser has been closed" in error_msg or "context" in error_msg.lower():
            return
        self._n_failures += 1
        if self._n_failures >= self._max_failures:
            self._n_failures = 0
            await self.restart()
    def on_success(self) -> None:
        """Reset failure count on success."""
        self._n_failures = 0
    async def crawl_url(self, url: str) -> CrawlResult:
        """Crawl a single URL with isolated context."""
        t0 = time.time()
        ctx = None
        try:
            await self.ensure_browser()
            async with self._lock:
                if self._browser is None:
                    raise RuntimeError("Browser not available")
                ctx = await self._browser.new_context()
            page = await ctx.new_page()
            try:
                result = await self._do_crawl(page, url, t0)
                self.on_success()
                return result
            finally:
                await page.close()
        except Exception as e:
            err_msg = str(e)
            log.error(f"Crawl error for {url}: {e}")
            await self.on_failure(err_msg)
            return CrawlResult(
                url=url,
                status=CrawlStatus.FAILED,
                error=err_msg,
                elapsed_sec=time.time() - t0,
            )
        finally:
            if ctx:
                try:
                    await ctx.close()
                except Exception:
                    pass
    async def _do_crawl(self, page: Page, url: str, t0: float) -> CrawlResult:
        """Perform actual crawl on page."""
        initial_bytes = 0
        rendered_bytes = 0
        async def on_response(resp: Response) -> None:
            nonlocal initial_bytes
            if initial_bytes == 0 and resp.request.resource_type == "document":
                try:
                    body = await resp.body()
                    initial_bytes = len(body)
                except Exception:
                    pass
        page.on("response", on_response)
        try:
            timeout_ms = int(self.cfg.page_timeout_sec * 1000)
            await page.goto(url, timeout=timeout_ms, wait_until="load")
            await page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception as e:
            if "timeout" in str(e).lower():
                log.warning(f"Timeout for {url}")
                try:
                    html = await page.content()
                    rendered_bytes = len(html.encode("utf-8"))
                except Exception:
                    pass
                return CrawlResult(
                    url=url,
                    status=CrawlStatus.TIMEOUT,
                    initial_html_bytes=initial_bytes,
                    rendered_html_bytes=rendered_bytes,
                    error=str(e),
                    elapsed_sec=time.time() - t0,
                )
            raise
        html = await page.content()
        rendered_bytes = len(html.encode("utf-8"))
        log.info(f"Crawled {url}: init={initial_bytes}, rendered={rendered_bytes}")
        return CrawlResult(
            url=url,
            status=CrawlStatus.SUCCESS,
            initial_html_bytes=initial_bytes,
            rendered_html_bytes=rendered_bytes,
            elapsed_sec=time.time() - t0,
        )

async def crawl_batch(
    urls: list[str],
    browser_mgr: BrowserManager,
    max_concurrent: int,
) -> list[CrawlResult]:
    """Crawl a batch of URLs concurrently."""
    sem = asyncio.Semaphore(max_concurrent)
    async def crawl_w_sem(url: str) -> CrawlResult:
        async with sem:
            return await browser_mgr.crawl_url(url)
    tasks = [asyncio.create_task(crawl_w_sem(u)) for u in urls]
    return await asyncio.gather(*tasks)
