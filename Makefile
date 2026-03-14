.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts


clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint: ## check style with black
	black waterfurnace tests

test: ## run tests on all Python versions with tox
	tox

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source waterfurnace -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/waterfurnace.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ waterfurnace
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: clean ## update version and trigger release workflow
	@echo "Current version: $$(grep '^version = ' pyproject.toml | cut -d'"' -f2)"
	@read -p "Enter new version: " version; \
	if [ -z "$$version" ]; then \
		echo "No version provided. Aborting."; \
		exit 1; \
	fi; \
	if ! echo "$$version" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$$'; then \
		echo "Error: Version must be in format X.Y.Z"; \
		exit 1; \
	fi; \
	echo "Updating version to $$version in pyproject.toml..."; \
	sed -i "s/^version = .*/version = \"$$version\"/" pyproject.toml; \
	echo ""; \
	echo "Please update CHANGELOG.md with changes for version $$version"; \
	read -p "Press Enter when CHANGELOG.md is updated..."; \
	git add pyproject.toml CHANGELOG.md; \
	git commit -m "Release version $$version"; \
	echo ""; \
	echo "Pushing to main branch..."; \
	git push origin main; \
	echo ""; \
	echo "✅ Release workflow triggered!"; \
	echo ""; \
	echo "The GitHub Actions workflow will:"; \
	echo "  1. Run tests on all Python versions"; \
	echo "  2. Build the package"; \
	echo "  3. Publish to PyPI"; \
	echo "  4. Create GitHub release with tag v$$version"; \
	echo ""; \
	echo "Monitor progress at: https://github.com/sdague/waterfurnace/actions"

dist: clean ## builds source and wheel package
	python -m build
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	pip install -e .
