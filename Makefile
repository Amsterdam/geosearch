.PHONY: help
help:
	@grep -F -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | perl -pe 's/^(\w+):(.+?)##/"  $$1:" . " " x (20 - length($$1))/e' | perl -pe 's/^## ?//'

## Makefile to perform all tasks for development.
##
## Install commands:
##

.PHONY: install
install: 								               ## Perform all install steps.
	if ! command -v uv >/dev/null 2>&1; \
	then echo "uv not found, installing..." \
	&& curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	uv sync
	uv run pre-commit install

##
## Package management:
##

.PHONY: upgrade
upgrade:                               ## Upgrade the dependencies.
	uv sync --upgrade

##
## Testing:
##

.PHONY: test
test:                                  ## Run the test-suite.
	uv run pytest --reuse-db --nomigrations .

.PHONY: test
retest:                                ## Run the failed tests again.
	uv run pytest --reuse-db --nomigrations -vvs --lf .

##
## Development tools:
##

format:                                ## Fix code-formatting of all files.
	uv run ruff check --fix-only .

lint:                                  ## Report linting errors for all files
	uv run ruff check .

type:								                   ## Show typing errors for all files
	uv run ty check
