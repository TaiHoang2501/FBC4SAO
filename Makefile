.PHONY: run dev test eval comparative-eval lint format clean frontend ui

run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && javac HollandRAGGUI.java && java HollandRAGGUI

ui: frontend

test:
	pytest tests/ -v

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
