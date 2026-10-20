set shell := ["pwsh", "-NoLogo", "-NoProfile", "-Command"]

default: check

install:
    uv sync --extra dev

test:
    uv run --extra dev pytest --junitxml=artifacts/junit.xml --cov=vizaio_conjure --cov-report=term-missing --cov-report=xml:artifacts/coverage.xml

lint:
    uv run --extra dev ruff check .

format:
    uv run --extra dev ruff format --check .

typecheck:
    uv run --extra dev pyrefly check

prek:
    uvx prek run --all-files

check: lint format typecheck test

serve path="examples/smoke" bind="0.0.0.0" port="8765":
    uv run vizaio-conjure serve {{path}} --bind {{bind}} --port {{port}}
