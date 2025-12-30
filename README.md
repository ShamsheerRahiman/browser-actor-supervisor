# Browser Actor Supervisor

A robust, concurrent web crawler designed to drive Playwright browsers with supervisor-like resilience. It employs an actor model to orchestrate domain-polite crawling while adapting to system resource availability.

## System Architecture

Instead of naive concurrency, this system acts as a supervisor:

1.  **Actor-Based Orchestration**: A central `CrawlerActor` manages the lifecycle of the crawl, ensuring clean shutdowns and error isolation.
2.  **Domain-Polite Scheduling**:
    -   The **Scheduler** maintains separate queues for each domain.
    -   Enforces a strict **1-minute cooldown** between requests to the *same* domain to avoid being blocked.
    -   Maximizes concurrency by aggressively fetching URLs from *different* domains in parallel.
3.  **Resilient Browser Management**:
    -   Browsers are treated as cattle, not pets.
    -   The **Browser Manager** isolates every single page visit in a fresh context (no cookie/cache leakage).
    -   Automatically detects crashes or freezes and **restarts** the entire browser process after 3 consecutive failures.
4.  **Adaptive Resource Monitoring**:
    -   The **Monitor** checks real-time CPU and RAM usage before launching every new tab.
    -   Throttles concurrency dynamically if CPU > 80% or RAM > 80% to prevent system lockups.

## Setup

### Using uv (Recommended)

This project uses modern Python 3.14 features.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and sync dependencies
uv venv --python 3.14 .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
uv pip install -r pyproject.toml
playwright install chromium
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
pip install -r pyproject.toml
playwright install chromium
```

## Usage

### Run the Crawler

The crawler accepts an optional number of URLs to visit (default 5) and a custom file path.

```bash
# Default (crawls 5 URLs from 2kurls.txt)
python -m src.crawler.main

# Crawl 50 URLs
python -m src.crawler.main 50

# Crawl 100 URLs from a custom file
python -m src.crawler.main 100 my_urls.txt
```

### Generate Statistics

After a crawl, generate comprehensive CDF analyses and graphs:

```bash
python stats/generate_stats.py
```

This commands reads `crawl_results.json` and populates the `stats/` folder.

## Configuration

Configuration is defined in `CrawlerConfig` (`src/crawler/types.py`). You can modify defaults there:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `domain_delay_sec` | 60.0s | Mandatory wait time between requests to the same domain. |
| `page_timeout_sec` | 60.0s | Hard timeout for page load and rendering. |
| `cpu_threshold` | 80.0% | Pause new tabs if system CPU usage exceeds this. |
| `mem_threshold` | 80.0% | Pause new tabs if system RAM usage exceeds this. |
| `min_mem_avail_mb` | 512MB | Minimum free RAM required to launch a tab. |

## Output

### Data (`crawl_results.json`)
A JSON array containing the raw data for every visited URL:
-   `url`: The target URL.
-   `status`: `SUCCESS`, `TIMEOUT`, or `FAILED`.
-   `initial_html_bytes`: Size of the raw HTTP response body (before JS).
-   `rendered_html_bytes`: Size of the DOM after JS execution (full page load).
-   `elapsed_sec`: Total time taken for the attempt.

### Analysis (`stats/`)
-   `ANALYSIS.md`: A summary report of the crawl metrics.
-   `*_cdf.png`: Visual Cumulative Distribution Function (CDF) plots showing the distribution of data sizes across the dataset.

## Project Structure

```
src/crawler/
├── actor.py        # Lightweight actor framework (supervisor pattern)
├── main.py         # Entry point & orchestration logic
├── browser.py      # Resilient browser lifecycle & efficient context management
├── scheduler.py    # Domain-aware prioritization queue
├── monitor.py      # System resource watcher
└── types.py        # Configuration classes & type definitions

stats/
├── generate_stats.py # Analysis & plotting script
└── ...               # Generated reports and graphs
```

---

*Disclaimer: This project code and documentation were generated with the assistance of AI.*
