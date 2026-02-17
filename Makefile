#
# Colors
#

# Define ANSI color codes
RESET_COLOR   = \033[m

BLUE       = \033[1;34m
YELLOW     = \033[1;33m
GREEN      = \033[1;32m
RED        = \033[1;31m
BLACK      = \033[1;30m
MAGENTA    = \033[1;35m
CYAN       = \033[1;36m
WHITE      = \033[1;37m

DBLUE      = \033[0;34m
DYELLOW    = \033[0;33m
DGREEN     = \033[0;32m
DRED       = \033[0;31m
DBLACK     = \033[0;30m
DMAGENTA   = \033[0;35m
DCYAN      = \033[0;36m
DWHITE     = \033[0;37m

BG_WHITE   = \033[47m
BG_RED     = \033[41m
BG_GREEN   = \033[42m
BG_YELLOW  = \033[43m
BG_BLUE    = \033[44m
BG_MAGENTA = \033[45m
BG_CYAN    = \033[46m

# Name some of the colors
COM_COLOR   = $(DBLUE)
OBJ_COLOR   = $(DCYAN)
OK_COLOR    = $(DGREEN)
ERROR_COLOR = $(DRED)
WARN_COLOR  = $(DYELLOW)
NO_COLOR    = $(RESET_COLOR)

OK_STRING    = "[OK]"
ERROR_STRING = "[ERROR]"
WARN_STRING  = "[WARNING]"

define banner
    @echo "  $(BLUE)__________$(RESET_COLOR)"
    @echo "$(BLUE) |$(RED)BIG🌲LOCAL$(RESET_COLOR)$(BLUE)|$(RESET_COLOR)"
    @echo "$(BLUE) |&&& ======|$(RESET_COLOR)"
    @echo "$(BLUE) |=== ======|$(RESET_COLOR)  $(DWHITE)This is a $(RESET_COLOR)$(BG_RED)$(WHITE)Big Local News$(RESET_COLOR)$(DWHITE) automation$(RESET_COLOR)"
    @echo "$(BLUE) |=== == %%%|$(RESET_COLOR)"
    @echo "$(BLUE) |[_] ======|$(RESET_COLOR)  $(1)"
    @echo "$(BLUE) |=== ===!##|$(RESET_COLOR)"
    @echo "$(BLUE) |__________|$(RESET_COLOR)"
    @echo ""
endef

#
# Python helpers
#

UV := uv run
PYTHON := $(UV) python -W ignore

#
# Tests
#

lint: ## run the linter
	$(call banner,        💅 Linting code 💅)
	@$(UV) flake8 ./


test: ## run all tests
	$(call banner,       🤖 Running tests 🤖)
	@$(UV) pytest -sv


test-all: ## run tests across Python 3.9, 3.10, 3.11
	$(call banner,  🤖 Running tests (all versions) 🤖)
	@for version in 3.9 3.10 3.11; do \
		echo "\n$(CYAN)━━━ Python $$version ━━━$(RESET_COLOR)"; \
		uv run --python $$version pytest -sv || exit 1; \
	done

#
# Releases
#

check-release: ## check release for potential errors
	$(call banner,      🔎 Checking release 🔎)
	@$(UV) twine check dist/*


build-release: ## builds source and wheel package
	$(call banner,      📦 Building release 📦)
	@$(UV) python -m build
	@ls -l dist

#
# Docs
#

serve-docs: ## start the documentation test server
	$(call banner,         📃 Serving docs 📃)
	cd docs && uv run --group docs sphinx-autobuild -b html -d _build/doctrees . _build/html


test-docs: ## build the docs as html
	$(call banner,        📃 Building docs 📃)
	cd docs && uv run --group docs sphinx-build -b html -d _build/doctrees . _build/html

#
# Extras
#

format: ## automatically format Python code with black
	$(call banner,       🪥 Cleaning code 🪥)
	@$(UV) black .


help: ## Show this help. Example: make help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


# Mark all the commands that don't have a target
.PHONY: help \
        build-release \
        check-release \
        coverage \
        dist \
        format \
        lint \
        mypy \
        release \
        run \
        serve-docs \
        test \
        test-all \
        test-docs \
        test-release
