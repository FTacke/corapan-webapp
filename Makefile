.PHONY: help install dev test clean index bls proxy-test

help:
	@echo "CO.RA.PAN Development Targets"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install Python dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start Flask dev server (port 8000)"
	@echo "  make test             - Run pytest suite"
	@echo "  make clean            - Clean cache/build artifacts"
	@echo ""
	@echo "BlackLab Indexing:"
	@echo "  make index            - Build BlackLab index from corpus"
	@echo "  make index-dry        - Dry-run export (show sample)"
	@echo "  make bls              - Start BlackLab Server (port 8081)"
	@echo "  make proxy-test       - Quick proxy health check"
	@echo ""
	@echo "Docs:"
	@echo "  make docs             - Open documentation locally"
	@echo ""

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

dev:
	@echo "Starting Flask dev server (http://localhost:8000)..."
	FLASK_ENV=development python -m src.app.main

test:
	@echo "Running tests..."
	pytest -v

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

# BlackLab Index Build
index:
	@echo "Building BlackLab index..."
	@echo "This will:"
	@echo "  1. Export JSON corpus to TSV"
	@echo "  2. Generate docmeta.jsonl"
	@echo "  3. Build index → /data/blacklab_index"
	@echo ""
	bash scripts/build_blacklab_index.sh tsv 4

index-dry:
	@echo "Dry-run export (showing sample)..."
	python -m src.scripts.blacklab_index_creation \
		--in media/transcripts \
		--out /data/bl_input \
		--format tsv \
		--docmeta /data/bl_input/docmeta.jsonl \
		--workers 4 \
		--limit 3 \
		--dry-run

# BlackLab Server Control
bls:
	@echo "Starting BlackLab Server (http://127.0.0.1:8081)..."
	@echo "This will run in background. View logs: tail -f logs/bls/server.log"
	@echo ""
	bash scripts/run_bls.sh 8081 2g 512m

proxy-test:
	@echo "Testing BlackLab proxy connection..."
	@curl -s http://localhost:8000/bls/ | python -m json.tool || echo "Proxy not responding"

docs:
	@echo "Opening documentation at docs/index.md..."
	@echo "Rendered markdown available in browser (if running live server)"
	@python -c "import webbrowser; webbrowser.open('file://$(PWD)/docs/index.md')" 2>/dev/null || echo "Manual: open docs/index.md"
