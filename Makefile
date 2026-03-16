test:
	python -Werror -m unittest

autotest:
	find . -name \*.py -not -path .\/.v\* | entr make test

.PHONY: test

dist/: pyproject.toml simpleeval.py README.rst
	hatch build
	twine check dist/*

pypi: test dist/
	twine check dist/*
	twine upload dist/*

clean:
	rm -rf build
	rm -rf dist

coverage:
	coverage run python -m unittest

lint:
	ruff check simpleeval.py tests/
	ruff format --check simpleeval.py tests/
	mypy simpleeval.py tests/

format:
	ruff check --fix-only simpleeval.py tests/
	ruff format simpleeval.py tests/
