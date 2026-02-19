# Makefile
.PHONY: install test run-server benchmark clean

install:
	pip install -e .[dev,xerv]

test:
	pytest tests/ -v

run-server:
	uvicorn hanerma.server.main:app --reload --host 0.0.0.0 --port 8000

benchmark:
	python tests/benchmarks/run_gaia.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
