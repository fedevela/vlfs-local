.PHONY: setup run clean test coverage

setup:
	@echo "Syncing workspace dependencies..."
	uv sync

run:
	@echo "Running main app..."
	uv run python src/main.py

test:
	@echo "Running tests..."
	uv run pytest src/ packages/

coverage:
	@echo "Running tests with coverage..."
	uv run pytest --cov=packages/hello/src/hello --cov=packages/marco_polo/src/marco_polo --cov=src --cov-report=term-missing src/ packages/

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".venv" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
