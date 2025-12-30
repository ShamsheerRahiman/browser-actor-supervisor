# Browser Actor Supervisor

MVP web crawler using Playwright and Python 3.14.

## Setup

```bash
uv venv --python 3.14 .venv
source .venv/bin/activate
uv pip install -r pyproject.toml
playwright install chromium
```

## Usage

```bash
python -m src.crawler.main
```
