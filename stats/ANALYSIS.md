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
