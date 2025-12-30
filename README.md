# Browser Actor Supervisor

MVP web crawler that drives Playwright browsers to visit a list of URLs using Python 3.14, asyncio, and a lightweight actor runtime.

## Features

- **Per-domain delay**: 1-minute delay between requests to same domain.
- **Cross-domain concurrency**: Maximally concurrent across different domains.
- **Resource monitoring**: Monitors CPU/memory to throttle tab launches.
- **Browser supervision**: Automatically restarts browsers on failure.
- **HTML byte capture**: Saves initial HTML (before JS) and rendered HTML (after JS).

## Requirements

- Python 3.14+
- uv package manager (preferred) or venv/pip
- Playwright (Chromium installed via `playwright install chromium`)

## Setup (uv)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --python 3.14 .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
uv pip install -r pyproject.toml
playwright install chromium
```

## Setup (pip/venv)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

pip install -r <(python - <<'PY'
import tomllib
deps=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']
print('\n'.join(deps))
PY
)
playwright install chromium
```

## Usage

```bash
# Run with 5 URLs (default)
python -m src.crawler.main

# Run with custom count
python -m src.crawler.main 10

# Run with custom URL file
python -m src.crawler.main 100 my_urls.txt

# Generate stats from results
python -m src.crawler.stats crawl_results.json
```

## Configuration

Edit `CrawlerConfig` in [src/crawler/main.py](src/crawler/main.py):

- `domain_delay_sec`: Delay between same-domain requests (default: 60s)
- `page_timeout_sec`: Page load timeout (default: 60s)
- `cpu_threshold`: Max CPU% before throttling (default: 80%)
- `mem_threshold`: Max memory% before throttling (default: 85%)
- `min_mem_avail_mb`: Minimum free memory to allow new tabs (default: 512 MB)

## Output

- `crawl_results.json`: JSON array of crawl results with:
  - `url`: Crawled URL
  - `status`: SUCCESS, TIMEOUT, or FAILED
  - `initial_html_bytes`: Bytes before JS rendering
  - `rendered_html_bytes`: Bytes after full page load
  - `elapsed_sec`: Time taken

## Type Checking

```bash
basedpyright src/
```

## Project Structure

```
src/crawler/
├── __init__.py     # Package init
├── actor.py        # Lightweight actor runtime
├── main.py         # Entry point (orchestrator runs via actor)
├── browser.py      # Browser management & crawling
├── scheduler.py    # Domain-based URL scheduling
├── monitor.py      # CPU/memory monitoring
├── types.py        # Data types & config
└── stats.py        # Stats & CDF analysis
```
