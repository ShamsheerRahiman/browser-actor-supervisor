"""Generate stats and CDF plots from crawl results."""
import json
import sys
from pathlib import Path

def load_results(path: Path) -> list[dict]:
    """Load results from JSON file."""
    return json.loads(path.read_text())

def compute_cdf(values: list[int]) -> tuple[list[int], list[float]]:
    """Compute CDF from values."""
    if not values:
        return [], []
    sorted_v = sorted(values)
    n = len(sorted_v)
    cdf = [(i + 1) / n for i in range(n)]
    return sorted_v, cdf

def print_cdf_ascii(values: list[int], label: str, width: int = 50) -> None:
    """Print ASCII CDF plot."""
    if not values:
        print(f"No data for {label}")
        return
    sorted_v, cdf = compute_cdf(values)
    print(f"\n=== CDF: {label} ===")
    print(f"Min: {min(values):,} bytes")
    print(f"Max: {max(values):,} bytes")
    print(f"Median: {sorted_v[len(sorted_v)//2]:,} bytes")
    print(f"Mean: {sum(values)//len(values):,} bytes")
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    print("\nPercentiles:")
    for p in percentiles:
        idx = min(int(len(sorted_v) * p / 100), len(sorted_v) - 1)
        print(f"  p{p}: {sorted_v[idx]:,} bytes")
    print("\nDistribution (log scale):")
    import math
    if min(values) > 0:
        log_min = math.log10(min(values))
        log_max = math.log10(max(values))
        n_bins = 10
        bins = [0] * n_bins
        for v in values:
            if v > 0:
                bin_idx = min(int((math.log10(v) - log_min) / (log_max - log_min + 0.001) * n_bins), n_bins - 1)
                bins[bin_idx] += 1
        max_count = max(bins) if bins else 1
        for i, count in enumerate(bins):
            lo = 10 ** (log_min + i * (log_max - log_min) / n_bins)
            hi = 10 ** (log_min + (i + 1) * (log_max - log_min) / n_bins)
            bar = "#" * int(count / max_count * width)
            print(f"  {lo/1024:7.1f}K - {hi/1024:7.1f}K | {bar} ({count})")

def main() -> None:
    """Entry point."""
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("crawl_results.json")
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)
    results = load_results(path)
    n_total = len(results)
    by_status: dict[str, int] = {}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    print(f"=== Crawl Summary ===")
    print(f"Total URLs: {n_total}")
    for status, count in sorted(by_status.items()):
        print(f"  {status}: {count} ({100*count/n_total:.1f}%)")
    init_bytes = [r["initial_html_bytes"] for r in results if r["initial_html_bytes"] > 0]
    rend_bytes = [r["rendered_html_bytes"] for r in results if r["rendered_html_bytes"] > 0]
    print_cdf_ascii(init_bytes, "Initial HTML Bytes")
    print_cdf_ascii(rend_bytes, "Rendered HTML Bytes")
    times = [r["elapsed_sec"] for r in results]
    print(f"\n=== Timing ===")
    print(f"Total elapsed: {sum(times):.1f}s")
    print(f"Avg per URL: {sum(times)/len(times):.1f}s")
    print(f"Min: {min(times):.1f}s, Max: {max(times):.1f}s")

if __name__ == "__main__":
    main()
