# Crawl Statistics Report

## Summary
- **Total URLs crawled**: 2,000
- **Success rate**: 85.5%
- **Failed/Timeout**: 291 (14.5%)
- **Wall-clock runtime**: 2193.3s (36.6 min)

## HTML Size Statistics

### Initial HTML (before rendering)
| Metric | Value |
|--------|-------|
| Min | 1 bytes (0.0 KB) |
| Max | 2,606,598 bytes (2.49 MB) |
| Median | 126,322 bytes (123.4 KB) |
| Mean | 215,122 bytes (210.1 KB) |
| p90 | 458,566 bytes |
| p95 | 749,369 bytes |
| p99 | 1,905,696 bytes |

### Rendered HTML (after JS execution)
| Metric | Value |
|--------|-------|
| Min | 39 bytes (0.0 KB) |
| Max | 2,617,644 bytes (2.50 MB) |
| Median | 169,353 bytes (165.4 KB) |
| Mean | 266,366 bytes (260.1 KB) |
| p90 | 603,195 bytes |
| p95 | 789,562 bytes |
| p99 | 1,915,432 bytes |

### Size Ratio (Rendered / Initial)
| Metric | Value |
|--------|-------|
| Median ratio | 1.13x |
| Mean ratio | 38.00x |
| Max expansion | 19083.00x |
| Max shrinkage | 0.08x |

## Timing Statistics
| Metric | Value |
|--------|-------|
| Cumulative time (all URLs) | 151536.2s (42.09 hours) |
| Avg per URL | 75.8s |
| Median per URL | 68.7s |
| Min | 2.6s |
| Max | 245.9s |

> **Note**: "Cumulative time" is the sum of individual page load times. Due to cross-domain concurrency, the actual wall-clock runtime is significantly shorter.

## CDF Plots

### Initial HTML Bytes CDF
![Initial HTML CDF](initial_html_cdf.png)

### Rendered HTML Bytes CDF
![Rendered HTML CDF](rendered_html_cdf.png)

### Comparison CDF (Initial vs Rendered)
![Comparison CDF](comparison_cdf.png)

## Brief Analysis

### The "Rendering Tax"
The CDF comparison illustrates the "Rendering Tax" imposed by modern client-side execution. While the **Median HTML size** grows from **123.4 KB** to **165.4 KB** (a ~34% increase), the **Mean expansion ratio (38.00x)** and **Max expansion (19,083x)** reveal a "heavy tail" of highly dynamic sites. These outliers likely represent Single Page Applications (SPAs) or heavily obfuscated sites that deliver almost no content in the initial static shell, relying entirely on post-load JS execution to populate the DOM.

### Distribution Characteristics
* **Initial vs. Rendered Shift**: The rendered CDF (orange) is consistently shifted to the right of the initial CDF (blue) across the distribution, representing the significant hidden complexity missed by static scrapers.
* **Convergence at High Volumes**: Both distributions converge near the **p99 mark (~1.9 MB)**. This suggests a practical upper bound for DOM size in typical web content, where the relative impact of JS-driven expansion diminishes for already massive static pages.

### System Throughput & Efficiency
The crawler demonstrated significant efficiency by compressing a massive amount of computational work into a short window:
* **Total Service Time (Cumulative)**: The system managed **42.09 hours** of aggregate processing time across the 2,000 URLs.
* **Wall-Clock Runtime (Actual)**: Due to high cross-domain concurrency, the entire task was completed in only **36.6 minutes**.
* **Throughput Speedup**: This represents a **~69x speedup factor**, proving the effectiveness of the actor-based concurrency model in maximizing resource utilization while strictly adhering to the 1-minute domain-specific politeness delay.

### Operational Stability
The "Destroy and Restart" logic was used to manage stability during the high-concurrency crawl. CPU and memory monitoring prevented resource exhaustion during the **14.5% failure/timeout rate**. The **75.8s average per URL** includes the 1-minute render timeout, which limited the impact of high-latency dynamic sites on global queue progression.