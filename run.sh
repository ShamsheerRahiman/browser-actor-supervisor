#!/usr/bin/env bash
# Setup and run the crawler in WSL with Python 3.14.
set -e
cd "$(dirname "$0")"
# Install uv if needed
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env"
fi
# Create venv with py3.14
uv venv --python 3.14 .venv
source .venv/bin/activate
# Install deps
uv pip install -e .
uv pip install playwright
playwright install chromium
# Run crawler
python -m src.crawler.main "$@"
