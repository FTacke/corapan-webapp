.PHONY: help install sync lockfiles dev test lint format e2e clean

help:
	@echo "CO.RA.PAN app targets"
	@echo ""
	@echo "  make install   - Install runtime dependencies"
	@echo "  make sync      - Sync the local environment with requirements-dev.txt via uv"
	@echo "  make lockfiles - Recompile requirements.txt and requirements-dev.txt"
	@echo "  make dev       - Start the canonical root dev workflow"
	@echo "  make test      - Run the fast pytest suite"
	@echo "  make lint      - Run ruff"
	@echo "  make format    - Run ruff format"
	@echo "  make e2e       - Run Playwright tests"
	@echo "  make clean     - Remove local caches"

install:
	pip install -r requirements.txt

sync:
	powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1 -Dev

lockfiles:
	powershell -ExecutionPolicy Bypass -File .\scripts\refresh-lockfiles.ps1

dev:
	powershell -ExecutionPolicy Bypass -File ..\scripts\dev-start.ps1

test:
	pytest -v

lint:
	ruff check src tests

format:
	ruff format src tests

e2e:
	npm run test:e2e

clean:
	@echo "Remove Python and test caches manually if needed."
