include .env
export

VERSION 		:= v0.1.0
# GIT_HASH		:= $(shell git rev-parse --short HEAD)
PYTHON_FILES   	:= $(shell find . -type f -name '*.py' \
	-not -path "./venv/*" \
	-not -path "./.venv/*" \
)
CURR_DIR		:= $(shell pwd)
TEST_FILE 		:= $(CURR_DIR)/tests/test_*.py

#################################
# HELP
#################################

.PHONY: help
help: ### Display this help screen.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

#################################
# LINTING AND FORMATTING
#################################

.PHONY: lint format
lint format: ### Lint and format the code.
	@uv run ruff check --fix $(PYTHON_FILES)
	@uv run ruff format $(PYTHON_FILES)

#################################
# RUNNING AGENT
#################################

.PHONY: local_run
local_run: lint ### Run the agent locally.
	@uv run src/agent.py run --file_path=./tests/fixtures/built-multi-agent-research-system.md --keep_original=True

#################################
# TESTING
#################################

.PHONY: test
test: ### Run unit tests. (pytest)
	@(export PYTHONPATH=${PYTHONPATH}:${CURR_DIR}/src && \
		uv run pytest -vv $(TEST_FILE))

#################################
# CLEANING
#################################
.PHONY: clean
clean: ### Clean the cache.
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
