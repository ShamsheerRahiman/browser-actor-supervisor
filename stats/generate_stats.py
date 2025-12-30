"""Generate stats and CDF plots from crawl results."""
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('seaborn-v0_8-darkgrid')

STATS_DIR = Path(__file__).parent
RESULTS_FILE = STATS_DIR.parent / "crawl_results.json"

def load_results(path: Path) -> list[dict]:
    """Load results from JSON file."""
    return json.loads(path.read_text())

def compute_cdf(values: list) -> tuple[np.ndarray, np.ndarray]:
    """Compute CDF from values."""
    sorted_v = np.sort(values)
    cdf = np.arange(1, len(sorted_v) + 1) / len(sorted_v)
    return sorted_v, cdf

def plot_cdf(values: list, title: str, xlabel: str, output_path: Path, color: str = "#2E86AB") -> None:
    """Generate and save CDF plot."""
    fig, ax = plt.subplots(figsize=(10, 6))
    x, y = compute_cdf(values)
    ax.plot(x, y, linewidth=2, color=color)
    ax.fill_between(x, y, alpha=0.3, color=color)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel("CDF (Cumulative Probability)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    percentiles = [25, 50, 75, 90, 95]
    for p in percentiles:
        idx = int(len(x) * p / 100)
        val = x[idx] if idx < len(x) else x[-1]
        ax.axhline(y=p/100, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
        ax.annotate(f'p{p}: {val/1024:.0f}KB', xy=(val, p/100), fontsize=9, color='gray')
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_path}")

def plot_cdf_log(values: list, title: str, xlabel: str, output_path: Path, color: str = "#2E86AB") -> None:
    """Generate and save CDF plot with log scale x-axis."""
    fig, ax = plt.subplots(figsize=(10, 6))
    x, y = compute_cdf(values)
    ax.plot(x, y, linewidth=2, color=color)
    ax.fill_between(x, y, alpha=0.3, color=color)
    ax.set_xscale('log')
    ax.set_xlabel(xlabel + " (log scale)", fontsize=12)
    ax.set_ylabel("CDF (Cumulative Probability)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3, which='both')
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_path}")

def plot_comparison_cdf(init_bytes: list, rend_bytes: list, output_path: Path) -> None:
    """Generate comparison CDF plot of initial vs rendered HTML."""
    fig, ax = plt.subplots(figsize=(10, 6))
    x1, y1 = compute_cdf(init_bytes)
    x2, y2 = compute_cdf(rend_bytes)
    ax.plot(x1, y1, linewidth=2, color="#2E86AB", label="Initial HTML")
    ax.plot(x2, y2, linewidth=2, color="#E94F37", label="Rendered HTML")
    ax.fill_between(x1, y1, alpha=0.2, color="#2E86AB")
    ax.fill_between(x2, y2, alpha=0.2, color="#E94F37")
    ax.set_xscale('log')
    ax.set_xlabel("HTML Size (bytes, log scale)", fontsize=12)
    ax.set_ylabel("CDF (Cumulative Probability)", fontsize=12)
    ax.set_title("CDF Comparison: Initial vs Rendered HTML", fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.05)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3, which='both')
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_path}")



def generate_analysis(results: list, by_status: dict, init_bytes: list, rend_bytes: list, times: list) -> str:
    """Generate analysis markdown."""
    n = len(results)
    success_rate = by_status.get('SUCCESS', 0) / n * 100
    valid_pairs = [(r['initial_html_bytes'], r['rendered_html_bytes']) for r in results if r['initial_html_bytes'] > 0 and r['rendered_html_bytes'] > 0]
    ratio = np.array([r[1] / r[0] for r in valid_pairs])
    analysis = f"""# Crawl Statistics Report

## Summary
- **Total URLs crawled**: {n:,}
- **Success rate**: {success_rate:.1f}%
- **Failed/Timeout**: {by_status.get('FAILED', 0) + by_status.get('TIMEOUT', 0):,} ({100-success_rate:.1f}%)

## HTML Size Statistics

### Initial HTML (before rendering)
| Metric | Value |
|--------|-------|
| Min | {min(init_bytes):,} bytes ({min(init_bytes)/1024:.1f} KB) |
| Max | {max(init_bytes):,} bytes ({max(init_bytes)/1024/1024:.2f} MB) |
| Median | {int(np.median(init_bytes)):,} bytes ({np.median(init_bytes)/1024:.1f} KB) |
| Mean | {int(np.mean(init_bytes)):,} bytes ({np.mean(init_bytes)/1024:.1f} KB) |
| p90 | {int(np.percentile(init_bytes, 90)):,} bytes |
| p95 | {int(np.percentile(init_bytes, 95)):,} bytes |
| p99 | {int(np.percentile(init_bytes, 99)):,} bytes |

### Rendered HTML (after JS execution)
| Metric | Value |
|--------|-------|
| Min | {min(rend_bytes):,} bytes ({min(rend_bytes)/1024:.1f} KB) |
| Max | {max(rend_bytes):,} bytes ({max(rend_bytes)/1024/1024:.2f} MB) |
| Median | {int(np.median(rend_bytes)):,} bytes ({np.median(rend_bytes)/1024:.1f} KB) |
| Mean | {int(np.mean(rend_bytes)):,} bytes ({np.mean(rend_bytes)/1024:.1f} KB) |
| p90 | {int(np.percentile(rend_bytes, 90)):,} bytes |
| p95 | {int(np.percentile(rend_bytes, 95)):,} bytes |
| p99 | {int(np.percentile(rend_bytes, 99)):,} bytes |

### Size Ratio (Rendered / Initial)
| Metric | Value |
|--------|-------|
| Median ratio | {np.median(ratio):.2f}x |
| Mean ratio | {np.mean(ratio):.2f}x |
| Max expansion | {np.max(ratio):.2f}x |
| Max shrinkage | {np.min(ratio):.2f}x |

## Timing Statistics
| Metric | Value |
|--------|-------|
| Total elapsed | {sum(times):.1f}s ({sum(times)/3600:.2f} hours) |
| Avg per URL | {np.mean(times):.1f}s |
| Median | {np.median(times):.1f}s |
| Min | {min(times):.1f}s |
| Max | {max(times):.1f}s |

## CDF Plots

### Initial HTML Bytes CDF
![Initial HTML CDF](initial_html_cdf.png)

### Rendered HTML Bytes CDF
![Rendered HTML CDF](rendered_html_cdf.png)

### Comparison CDF (Initial vs Rendered)
![Comparison CDF](comparison_cdf.png)
"""
    return analysis

def main() -> None:
    """Entry point."""
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULTS_FILE
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)
    results = load_results(path)
    print(f"Loaded {len(results)} results from {path}")
    by_status: dict[str, int] = {}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    init_bytes = [r["initial_html_bytes"] for r in results if r["initial_html_bytes"] > 0]
    rend_bytes = [r["rendered_html_bytes"] for r in results if r["rendered_html_bytes"] > 0]
    times = [r["elapsed_sec"] for r in results]
    print(f"\nGenerating plots...")
    plot_cdf(init_bytes, "CDF: Initial HTML Size", "HTML Size (bytes)", STATS_DIR / "initial_html_cdf.png")
    plot_cdf_log(init_bytes, "CDF: Initial HTML Size (Log Scale)", "HTML Size", STATS_DIR / "initial_html_cdf_log.png")
    plot_cdf(rend_bytes, "CDF: Rendered HTML Size", "HTML Size (bytes)", STATS_DIR / "rendered_html_cdf.png", "#E94F37")
    plot_cdf_log(rend_bytes, "CDF: Rendered HTML Size (Log Scale)", "HTML Size", STATS_DIR / "rendered_html_cdf_log.png", "#E94F37")
    plot_comparison_cdf(init_bytes, rend_bytes, STATS_DIR / "comparison_cdf.png")

    analysis = generate_analysis(results, by_status, init_bytes, rend_bytes, times)
    (STATS_DIR / "ANALYSIS.md").write_text(analysis)
    print(f"Saved: {STATS_DIR / 'ANALYSIS.md'}")
    print("\nDone! All stats and plots generated.")

if __name__ == "__main__":
    main()
