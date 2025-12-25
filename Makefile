.PHONY: setup update-deps run clean test lint

# Python interpreter in virtual environment
PYTHON := .venv/bin/python
PIP := .venv/bin/pip
PIP_COMPILE := .venv/bin/pip-compile
PIP_SYNC := .venv/bin/pip-sync

setup: .venv
	@echo "🔧 Setting up environment..."
	cd scripts && ./setup.sh

.venv:
	@echo "🐍 Creating virtual environment..."
	python3 -m venv .venv
	$(PIP) install --upgrade pip pip-tools

update-deps: .venv
	@echo "📦 Updating dependencies..."
	$(PIP_COMPILE) requirements.in
	$(PIP_SYNC)

run:
	@echo "🚀 Starting Fog Node..."
	./run.sh

clean:
	@echo "🧹 Cleaning up..."
	rm -rf __pycache__ .venv generated_audio/*.wav
	rm -rf app/__pycache__ app/*/__pycache__

lint:
	@echo "🔍 Linting not configured yet (add ruff)"

test:
	@echo "🧪 No tests configured."
