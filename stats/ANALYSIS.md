# Crawl Statistics Report

## Summary
- **Total URLs crawled**: 2,000
- **Success rate**: 85.1%
- **Failed/Timeout**: 298 (14.9%)
- **Wall-clock runtime**: N/A

## HTML Size Statistics

### Initial HTML (before rendering)
| Metric | Value |
|--------|-------|
| Min | 1 bytes (0.0 KB) |
| Max | 2,606,002 bytes (2.49 MB) |
| Median | 126,313 bytes (123.4 KB) |
| Mean | 212,774 bytes (207.8 KB) |
| p90 | 453,766 bytes |
| p95 | 733,439 bytes |
| p99 | 1,895,445 bytes |

### Rendered HTML (after JS execution)
| Metric | Value |
|--------|-------|
| Min | 39 bytes (0.0 KB) |
| Max | 2,617,056 bytes (2.50 MB) |
| Median | 169,466 bytes (165.5 KB) |
| Mean | 266,643 bytes (260.4 KB) |
| p90 | 607,207 bytes |
| p95 | 799,435 bytes |
| p99 | 1,915,989 bytes |

### Size Ratio (Rendered / Initial)
| Metric | Value |
|--------|-------|
| Median ratio | 1.13x |
| Mean ratio | 36.74x |
| Max expansion | 19503.00x |
| Max shrinkage | 0.08x |

## Timing Statistics
| Metric | Value |
|--------|-------|
| Cumulative time (all URLs) | 148990.5s (41.39 hours) |
| Avg per URL | 74.5s |
| Median per URL | 66.6s |
| Min | 2.6s |
| Max | 251.2s |

> **Note**: "Cumulative time" is the sum of individual page load times. Due to cross-domain concurrency, the actual wall-clock runtime is significantly shorter.

## CDF Plots

### Initial HTML Bytes CDF
![Initial HTML CDF](initial_html_cdf.png)

### Rendered HTML Bytes CDF
![Rendered HTML CDF](rendered_html_cdf.png)

### Comparison CDF (Initial vs Rendered)
![Comparison CDF](comparison_cdf.png)
