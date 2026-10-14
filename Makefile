.PHONY: run dev test test-unit test-all eval comparative-eval verify verify-ci verify-smoke lint format clean frontend ui

PORT ?= 8001

run:
	uvicorn src.main:app --host 0.0.0.0 --port $(PORT)

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port $(PORT)

frontend:
	cd frontend && javac HollandRAGGUI.java && java HollandRAGGUI

ui: frontend

test:
	pytest tests/ -v -m "not external"

test-unit:
	pytest tests/ -v -m "not external"

test-metrics:
	pytest tests/test_evaluation_metrics.py -v

test-all:
	pytest tests/ -v

verify:
	python eval/verify_reproducibility.py

verify-ci:
	python eval/verify_reproducibility.py --ci

audit: verify-ci

verify-smoke:
	python eval/verify_reproducibility.py --smoke-eval

eval:
	python eval/thesis_eval.py

comparative-eval:
	python eval/comparative_eval.py

lint:
	ruff check src/ eval/ tests/

format:
	ruff format src/ eval/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
