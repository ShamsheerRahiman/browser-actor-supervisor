"""Resource monitoring for adaptive tab launching."""
import asyncio
import logging
import psutil
from .types import ResourceStats, CrawlerConfig

log = logging.getLogger(__name__)

class ResourceMonitor:
    """Monitors CPU/memory to decide if more tabs can launch."""
    def __init__(self, cfg: CrawlerConfig) -> None:
        self.cfg = cfg
        self._last_stats: ResourceStats | None = None
    def get_stats(self) -> ResourceStats:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        stats = ResourceStats(
            cpu_pct=cpu,
            mem_pct=mem.percent,
            mem_avail_mb=mem.available / (1024 * 1024),
        )
        self._last_stats = stats
        return stats
    def can_launch_more(self, current_tabs: int) -> bool:
        """Check if resources allow launching more tabs."""
        stats = self.get_stats()
        cpu_ok = stats.cpu_pct < self.cfg.cpu_threshold
        mem_ok = stats.mem_pct < self.cfg.mem_threshold
        avail_ok = stats.mem_avail_mb > self.cfg.min_mem_avail_mb
        ok = cpu_ok and mem_ok and avail_ok
        if not ok:
            reasons = []
            if not cpu_ok:
                reasons.append(f"cpu={stats.cpu_pct:.1f}%>{self.cfg.cpu_threshold}%")
            if not mem_ok:
                reasons.append(f"mem={stats.mem_pct:.1f}%>{self.cfg.mem_threshold}%")
            if not avail_ok:
                reasons.append(f"avail={stats.mem_avail_mb:.0f}MB<{self.cfg.min_mem_avail_mb}MB")
            log.warning(f"[throttle] tabs={current_tabs}, {', '.join(reasons)}")
        return ok
    async def wait_4_resources(self, current_tabs: int) -> None:
        """Wait until resources are available."""
        while not self.can_launch_more(current_tabs):
            log.info(f"Waiting for resources, stats={self._last_stats}")
            await asyncio.sleep(5.0)
