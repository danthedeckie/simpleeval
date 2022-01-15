test:
	python test_simpleeval.py

autotest:
	find . -name \*.py -not -path .\/.v\* | entr make test

.PHONY: test

dist/: setup.cfg simpleeval.py README.rst
	python -m build
	twine check dist/*

pypi: test dist/
	twine check dist/*
	twine upload dist/*

clean:
	rm -rf build
	rm -rf dist

coverage:
	coverage run test_simpleeval.py
